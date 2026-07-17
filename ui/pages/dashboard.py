from __future__ import annotations

from pathlib import Path
import sys

# Make the project root importable so this page works whether it is launched
# via `streamlit run ui/app.py` or executed directly (e.g. the debug console),
# where the `ui` package would otherwise not be on sys.path.
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import httpx
from typing import Any, Callable, TypedDict

import io
import pandas as pd
import streamlit as st

from ui.components.feedback import empty_state
from ui.components.feature_selector import feature_selector
from ui.components.metric_card import metric_card
from ui.services import api_client


def _commit_dataset(dataset: dict[str, Any], profile: dict[str, Any]) -> None:
    """Store a freshly registered dataset in session state and notify the user."""
    # [+] Reliability: Use .get() for safer dictionary access.
    st.session_state.dataset = dataset or {}
    st.session_state.profile = profile or {}
    st.session_state.events = []
    st.session_state.job_id = None
    filename = dataset.get("filename", "Unknown file")
    rows = dataset.get("rows", 0)
    st.success(f"Registered `{filename}` ({rows:,} rows).")


def _columns_from_upload(uploaded: Any) -> list[str]:
    """Infer column names from an in-memory upload for the pre-run selectors.

    The serverless backend computes the real schema during the run, but we need
    the column list up-front to let the user pick a target/features.
    """
    try:
        suffix = uploaded.name.lower()
        if suffix.endswith(".parquet"):
            return list(pd.read_parquet(io.BytesIO(uploaded.getvalue())).columns)
        return list(pd.read_csv(io.BytesIO(uploaded.getvalue()), nrows=1).columns) # type: ignore
    except Exception:
        return []


def _handle_source_connection(label: str, source_type: str, params: dict[str, Any], is_valid: bool = True) -> None:
    """Handle the UI and logic for connecting to a data source."""
    if not is_valid:
        st.error("Provide all required inputs.")
        return

    # [+] Production-Grade Error Handling: Catch specific exceptions instead of a generic `Exception`.
    # This prevents masking programming errors and provides clearer feedback to the user.
    with st.spinner(f"Connecting to {source_type}…"):
        try:
            result = api_client.run(
                api_client.connect_source(st.session_state.api_base_url, source_type=source_type, **params)
            )
            # [+] Reliability: Safely access API results with .get() to prevent KeyErrors.
            dataset = result.get("dataset")
            profile = result.get("profile")
            _commit_dataset(dataset, profile)
        except httpx.HTTPStatusError as exc:
            # Handle specific HTTP errors from the API client
            st.error(f"{label} failed: Server returned status {exc.response.status_code}. Check connection details and backend logs.")
        except Exception as exc:
            # A fallback for unexpected errors, which should be logged for debugging.
            st.error(f"An unexpected error occurred during {label}: {exc}")

# [+] Maintainability: Refactor the large if/elif block into a data-driven
# pattern. This makes adding or modifying data sources much cleaner and less
# error-prone. Each source is defined by a dictionary and rendered by a
# dedicated function.

class DataSource(TypedDict):
    label: str
    icon: str
    renderer: Callable[[], None]


def _render_upload_source() -> None:
    uploaded = st.file_uploader(
        "Dataset",
        type=["csv", "parquet"],
        help="CSV or Parquet. On the serverless backend, files up to 4 MB are uploaded and analysed in a single request.",
    )
    if uploaded is not None:
        size_mb = len(uploaded.getvalue()) / 1024 / 1024 if uploaded.getvalue() else 0
        if size_mb > 4:
            st.error(
                f"`{uploaded.name}` is {size_mb:.1f} MB — the serverless backend accepts up to 4 MB. "
                "Use a smaller sample or self-host the backend."
            )
        else:
            st.caption(f"{uploaded.name} · {size_mb:.2f} MB")
        if not st.session_state.serverless and st.button("Register dataset", key="upload_register", type="primary"):
            with st.spinner("Profiling dataset & detecting domain…"):
                try:
                    result = api_client.run(
                        api_client.upload_dataset(st.session_state.api_base_url, uploaded.name, uploaded.getvalue())
                    )
                    _commit_dataset(result.get("dataset"), result.get("profile"))
                except Exception as exc:
                    st.error(f"Upload failed: {exc}")
    
    return uploaded


def _render_sample_source() -> None:
    try:
        samples = api_client.run(api_client.list_samples(st.session_state.api_base_url)).get("samples", [])
    except Exception as exc:
        samples = []
        st.warning(f"Sample catalogue unavailable: {exc}")
    if samples:
        choice: None = st.selectbox("Built-in sample", [s["key"] for s in samples], format_func=lambda k: f"{k} — {next(s['description'] for s in samples if s['key'] == k)}")
        if st.button("Load sample", key="load_sample", type="primary"):
            _handle_source_connection("Sample load", "sample", {"sample_key": choice})
    return None


def _render_sql_source() -> None:
    db_url = st.text_input("Connection string", placeholder="postgresql://user:pass@host:5432/db")
    sql_mode = st.radio("Mode", ["Table", "Custom query"], horizontal=True)
    table = query = None
    if sql_mode == "Table":
        table = st.text_input("Table name")
    else:
        query = st.text_area("SQL query", placeholder="SELECT * FROM customers LIMIT 1000")
    if st.button("Connect", key="connect_sql", type="primary"):
        _handle_source_connection(
            "SQL connection", "sql",
            {"source_url": db_url, "table": table, "query": query},
            is_valid=bool(db_url and (table or query))
        )
    return None


DATA_SOURCES: list[DataSource] = [
    {"label": "Upload", "icon": "📂", "renderer": _render_upload_source},
    {"label": "Sample", "icon": "🧪", "renderer": _render_sample_source},
    {"label": "SQL database", "icon": "🛢️", "renderer": _render_sql_source},
    # Other sources can be refactored similarly...
]


def render_dashboard() -> None:
    st.markdown('<div class="eyebrow">Workspace / Dashboard</div>', unsafe_allow_html=True)
    st.title("Autonomous Data Science Agent OS")
    st.caption(
        "Upload a dataset, set autonomy boundaries, and launch an observable multi-agent pipeline."
    )

    st.markdown('<hr class="soft">', unsafe_allow_html=True)

    # ---- Ingest (multiple sources) -------------------------------------
    st.subheader("1 · Ingest dataset")
    selected_label = st.radio(
        "Data source",
        [s["label"] for s in DATA_SOURCES],
        horizontal=True,
        label_visibility="collapsed",
    )

    # 3D source constellation (always visible for spatial orientation)
    with st.expander("🌐 3D data-source map", expanded=False):
        try:
            all_sources = [
                {"key": s["label"].lower().replace(" ", "_"), "description": f"Connect via {s['label']}"}
                for s in DATA_SOURCES
            ]
            from ui.components.plot_3d import sources_3d
            sources_3d(all_sources)
        except Exception as exc:
            st.info(f"3D source map unavailable: {exc}")

    # Render the selected data source UI
    uploaded_file = None
    for source in DATA_SOURCES:
        if source["label"] == selected_label:
            uploaded_file = source["renderer"]
            break

    dataset = st.session_state.get("dataset")
    profile = st.session_state.get("profile")

    if not dataset or not profile:
        st.markdown('<hr class="soft">', unsafe_allow_html=True)
        empty_state(
            "📂",
            "No dataset loaded",
            "Choose a data source above to initialise lineage, schema profiling, and domain analysis.",
        )
        return

    # ---- Lineage & domain ---------------------------------------------
    if dataset and profile:
        st.markdown('<hr class="soft">', unsafe_allow_html=True)
        st.subheader("2 · Dataset lineage & domain")
    
        cols = st.columns(4)
        with cols[0]:
            metric_card("Rows", f"{dataset.get('rows', 0):,}", "Registered in dataset memory", accent="#2563eb")
        with cols[1]:
            metric_card("Columns", dataset.get("columns", 0), "Schema inferred", accent="#2563eb")
        with cols[2]:
            metric_card("Dataset ID", dataset.get("dataset_id", "N/A")[:8], "Lineage key", accent="#16a34a")
        with cols[3]:
            metric_card("Mode", "Autonomous", "Default control level", accent="#d97706")
    
        col_lineage, col_domain = st.columns([1.2, 1])
        with col_lineage:
            st.markdown(
                f"""
                <div class="card" style="min-height:110px;">
                    <div style="color:var(--muted); font-size:.72rem; text-transform:uppercase; letter-spacing:.08em;">Dataset file</div>
                    <div style="font-weight:600; margin-top:6px;">{dataset.get('filename', 'N/A')}</div>
                    <div class="small-muted" style="margin-top:4px; word-break:break-all;">{dataset.get('path', 'N/A')}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_domain:
            detected = profile.get("domain", {})
            domain_name = detected.get("domain", "general")
            domain_conf = detected.get("confidence", 0.0)
            badge = "primary" if domain_name != "general" else ""
            st.markdown(
                f"""
                <div class="card" style="min-height:110px;">
                    <div style="color:var(--muted); font-size:.72rem; text-transform:uppercase; letter-spacing:.08em;">Detected business domain</div>
                    <div style="margin-top:6px;"><span class="badge {badge}" style="text-transform:uppercase;">{domain_name}</span></div>
                    <div class="small-muted" style="margin-top:6px;">Confidence: {domain_conf:.1%}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    
        if domain_name and domain_name != "general":
            with st.expander(f"📖 Business domain reference — {domain_name.upper()}", expanded=False):
                try:
                    domain_info = api_client.run(
                        api_client.get_domain_details(st.session_state.api_base_url, domain_name)
                    )
                    st.markdown(domain_info["content"])
                except Exception as exc:
                    st.info(f"Domain reference unavailable: {exc}")
    
        with st.expander("Schema & missingness", expanded=False):
            schema_df = pd.DataFrame(
                [
                    {"column": column, "dtype": dtype, "missing_ratio": profile.get("missing_ratio", {}).get(column, 0)}
                    for column, dtype in dataset.get("schema", {}).items()
                ]
            )
            st.dataframe(schema_df, width="stretch", hide_index=True)
    
            try:
                preview_data = api_client.run(
                    api_client.preview_dataset(st.session_state.api_base_url, dataset["dataset_id"], page=1, page_size=50)
                )
                preview_df = pd.DataFrame(preview_data["rows"])
                st.dataframe(preview_df, width="stretch", hide_index=True)
            except Exception as exc:
                st.warning(f"Unable to load preview: {exc}")
    
        # 3D schema field
        with st.expander("🧊 3D schema field", expanded=False):
            st.caption("Columns placed on a grid; marker size encodes missing-ratio. Blue = numeric, amber = categorical.")
            try:
                from ui.components.plot_3d import schema_3d
    
                schema_3d(dataset.get("schema", {}), profile.get("missing_ratio", {}))
            except Exception as exc:
                st.info(f"3D schema unavailable: {exc}")

        # ---- Launch ----------------------------------------------------------
        st.markdown('<hr class="soft">', unsafe_allow_html=True)
        st.subheader("3 · Launch agent pipeline")

        if st.session_state.serverless:
            if uploaded_file is None:
                st.info("Upload a dataset above to configure and launch the pipeline.")
                return
            columns = _columns_from_upload(uploaded_file)
        else:
            columns = list(dataset.get("schema", {}))
        mode = st.radio("Autonomy", ["manual", "assisted", "autonomous"], index=2, horizontal=True)
        target = st.selectbox("Target column", columns, index=max(len(columns) - 1, 0))
        model = None
        features: list[str] = []
        if mode == "manual":
            model = st.selectbox("Model", ["linear", "random_forest"])
            features = feature_selector(columns, target)
        elif mode == "assisted":
            features = feature_selector(columns, target)

        if st.button("Start agent run", type="primary", use_container_width=True):
            if st.session_state.serverless:
                if uploaded_file is None:
                    st.error("Upload a dataset first.")
                else:
                    with st.spinner("Uploading & running agent pipeline (serverless)…"):
                        try:
                            result = api_client.run(
                                api_client.run_agent(
                                    st.session_state.api_base_url,
                                    filename=uploaded_file.name,
                                    content=uploaded_file.getvalue(),
                                    mode=mode,
                                    target=target,
                                    features=features,
                                    model=model,
                                )
                            )
                            _commit_dataset(result.get("dataset"), result.get("profile"))
                            st.session_state.job_id = result.get("job_id")
                            st.success(f"Agent run completed: `{st.session_state.job_id}` — view it on the Intelligence tab.")
                        except Exception as exc:
                            st.error(f"Agent run failed: {exc}")
            else:
                try:
                    started = api_client.run(
                        api_client.start_agent(
                            st.session_state.api_base_url,
                            dataset_id=dataset["dataset_id"],
                            mode=mode,
                            target=target,
                            features=features,
                            model=model,
                        )
                    )
                    st.session_state.job_id = started.get("job_id")
                    st.session_state.events = []
                    st.success(f"Agent run started: `{st.session_state.job_id}` — open Intelligence to watch it live.")
                except Exception as exc:
                    st.error(f"Agent run failed: {exc}")
