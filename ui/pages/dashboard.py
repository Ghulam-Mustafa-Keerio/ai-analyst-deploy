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
from typing import Any

import io
import pandas as pd
import streamlit as st

from ui.components.feedback import empty_state
from ui.components.feature_selector import feature_selector
from ui.components.metric_card import metric_card
from ui.services import api_client


def _commit_dataset(dataset: dict[str, Any], profile: dict[str, Any]) -> None:
    """Store a freshly registered dataset in session state and notify the user."""
    st.session_state.dataset = dataset
    st.session_state.profile = profile
    st.session_state.events = []
    st.session_state.job_id = None
    st.success(f"Registered `{dataset['filename']}` ({dataset['rows']:,} rows).")


def _columns_from_upload(uploaded) -> list[str]:
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

    with st.spinner(f"Connecting to {source_type}…"):
        try:
            result = api_client.run(
                api_client.connect_source(st.session_state.api_base_url, source_type=source_type, **params)
            )
            _commit_dataset(result["dataset"], result["profile"]) # type: ignore
        except Exception as exc:
            st.error(f"{label} failed: {exc}")


DATA_SOURCES = [
    {"label": "Upload", "icon": "📂"},
    {"label": "Sample", "icon": "🧪"},
    {"label": "SQL database", "icon": "🛢️"},
    {"label": "Remote URL", "icon": "🔗"},
    {"label": "JSON", "icon": "{}"},
    {"label": "Excel", "icon": "📊"},
    {"label": "Google Sheets", "icon": "📈"},
    {"label": "REST API", "icon": "🌐"},
    {"label": "MongoDB", "icon": "🍃"},
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
    source_tab = st.radio(
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

    uploaded = None
    if source_tab == "Upload":
        uploaded = st.file_uploader(
            "Dataset",
            type=["csv", "parquet"],
            help="CSV or Parquet. On the serverless backend, files up to 4 MB are uploaded and analysed in a single request.",
        )
        if uploaded is not None:
            size_mb = len(uploaded.getvalue()) / 1024 / 1024
            if size_mb > 4:
                st.error(
                    f"`{uploaded.name}` is {size_mb:.1f} MB — the serverless backend accepts up to 4 MB. "
                    "Use a smaller sample or self-host the backend."
                )
            else:
                st.caption(f"{uploaded.name} · {size_mb:.2f} MB")
    
    if st.session_state.serverless:
        dataset = st.session_state.dataset
        profile = st.session_state.profile
    else:
        if source_tab == "Upload" and uploaded is not None:
            if st.button("Register dataset", width="stretch", type="primary"):
                with st.spinner("Profiling dataset & detecting domain…"):
                    try:
                        result = api_client.run(
                            api_client.upload_dataset(
                                st.session_state.api_base_url, uploaded.name, uploaded.getvalue()
                            )
                        )
                        _commit_dataset(result["dataset"], result["profile"]) # type: ignore
                    except Exception as exc:
                        st.error(f"Upload failed: {exc}")

        elif source_tab == "Sample":
            try:
                samples = api_client.run(api_client.list_samples(st.session_state.api_base_url))["samples"]
            except Exception as exc:
                samples = [] # type: ignore
                st.warning(f"Sample catalogue unavailable: {exc}")
            if samples:
                choice = st.selectbox("Built-in sample", [s["key"] for s in samples], format_func=lambda k: f"{k} — {next(s['description'] for s in samples if s['key'] == k)}")
                if st.button("Load sample", width="stretch", type="primary"):
                    _handle_source_connection("Sample load", "sample", {"sample_key": choice})

        elif source_tab == "SQL database":
            db_url = st.text_input(
                "Connection string (sent to backend only)",
                placeholder="postgresql://user:pass@host:5432/db",
                help="SQLAlchemy URL. Credentials are sent to the backend only.",
            )
            sql_mode = st.radio("Mode", ["Table", "Custom query"], horizontal=True)
            table = query = None
            if sql_mode == "Table":
                table = st.text_input("Table name")
            else:
                query = st.text_area("SQL query", placeholder="SELECT * FROM customers LIMIT 1000")
            if st.button("Connect", width="stretch", type="primary"):
                _handle_source_connection(
                    "SQL connection", "sql", # type: ignore
                    {"source_url": db_url, "table": table, "query": query},
                    is_valid=bool(db_url and (table or query))
                )

        elif source_tab == "Remote URL":
            url = st.text_input("Dataset URL", placeholder="https://example.com/data.csv")
            if st.button("Fetch", width="stretch", type="primary"):
                _handle_source_connection("Fetch", "url", {"source_url": url}, is_valid=bool(url))

        elif source_tab == "JSON":
            json_url = st.text_input("JSON path or URL", placeholder="/path/to/data.json or https://api.example.com/rows")
            if st.button("Load JSON", width="stretch", type="primary"):
                _handle_source_connection("JSON load", "json", {"source_url": json_url}, is_valid=bool(json_url))

        elif source_tab == "Excel":
            excel_url = st.text_input("Excel path or URL", placeholder="/path/to/book.xlsx or https://example.com/book.xlsx")
            sheet = st.text_input("Sheet name or index", value="0")
            if st.button("Load Excel", width="stretch", type="primary"):
                _handle_source_connection(
                    "Excel load", "excel",
                    {"source_url": excel_url, "table": sheet or "0"},
                    is_valid=bool(excel_url)
                )

        elif source_tab == "Google Sheets":
            sheets_url = st.text_input(
                "Google Sheets link",
                placeholder="https://docs.google.com/spreadsheets/d/ID/edit#gid=0",
            )
            if st.button("Load Sheet", width="stretch", type="primary"):
                _handle_source_connection("Sheet load", "sheets", {"source_url": sheets_url}, is_valid=bool(sheets_url)) # type: ignore

        elif source_tab == "REST API":
            rest_url = st.text_input("REST endpoint", placeholder="https://api.example.com/items")
            data_key = st.text_input("JSON data key (optional)", placeholder="data")
            if st.button("Fetch API", width="stretch", type="primary"):
                _handle_source_connection(
                    "REST load", "rest", # type: ignore
                    {"source_url": rest_url, "data_key": data_key or None},
                    is_valid=bool(rest_url)
                )

        elif source_tab == "MongoDB":
            mongo_url = st.text_input(
                "MongoDB connection string (sent to backend only)",
                placeholder="mongodb://user:pass@host:27017/db",
                help="Credentials are sent to the backend only.",
            )
            mongo_coll = st.text_input("Collection name")
            if st.button("Connect", width="stretch", type="primary"):
                _handle_source_connection(
                    "MongoDB connection", "mongo", # type: ignore
                    {"source_url": mongo_url, "table": mongo_coll},
                    is_valid=bool(mongo_url and mongo_coll)
                )

        dataset = st.session_state.dataset
        profile = st.session_state.profile

    if not dataset or not profile:
        if st.session_state.serverless and uploaded is not None:
            pass
        else:
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
        metric_card("Rows", f"{dataset['rows']:,}", "Registered in dataset memory", accent="#2563eb")
    with cols[1]:
        metric_card("Columns", dataset["columns"], "Schema inferred", accent="#2563eb")
    with cols[2]:
        metric_card("Dataset ID", dataset["dataset_id"][:8], "Lineage key", accent="#16a34a")
    with cols[3]:
        metric_card("Mode", "Autonomous", "Default control level", accent="#d97706")

    col_lineage, col_domain = st.columns([1.2, 1])
    with col_lineage:
        st.markdown(
            f"""
            <div class="card" style="min-height:110px;">
                <div style="color:var(--muted); font-size:.72rem; text-transform:uppercase; letter-spacing:.08em;">Dataset file</div>
                <div style="font-weight:600; margin-top:6px;">{dataset['filename']}</div>
                <div class="small-muted" style="margin-top:4px; word-break:break-all;">{dataset['path']}</div>
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
                {"column": column, "dtype": dtype, "missing_ratio": profile["missing_ratio"].get(column, 0)}
                for column, dtype in dataset["schema"].items()
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

            schema_3d(dataset["schema"], profile.get("missing_ratio", {}))
        except Exception as exc:
            st.info(f"3D schema unavailable: {exc}")

    # ---- Launch ----------------------------------------------------------
    st.markdown('<hr class="soft">', unsafe_allow_html=True)
    st.subheader("3 · Launch agent pipeline")

    if st.session_state.serverless:
        if uploaded is None:
            st.info("Upload a dataset above to configure and launch the pipeline.")
            return
        columns = _columns_from_upload(uploaded)
    else:
        columns = list(dataset["schema"])
    mode = st.segmented_control("Autonomy", ["manual", "assisted", "autonomous"], default="autonomous")
    target = st.selectbox("Target column", columns, index=max(len(columns) - 1, 0))
    model = None
    features: list[str] = []
    if mode == "manual":
        model = st.selectbox("Model", ["linear", "random_forest"])
        features = feature_selector(columns, target)
    elif mode == "assisted":
        features = feature_selector(columns, target)

    if st.button("Start agent run", type="primary", width="stretch"):
        if st.session_state.serverless:
            if uploaded is None:
                st.error("Upload a dataset first.")
            else:
                with st.spinner("Uploading & running agent pipeline (serverless)…"):
                    try:
                        result = api_client.run(
                            api_client.run_agent(
                                st.session_state.api_base_url,
                                filename=uploaded.name,
                                content=uploaded.getvalue(),
                                mode=mode,
                                target=target,
                                features=features,
                                model=model,
                            )
                        )
                        st.session_state.job_id = result["job_id"]
                        st.session_state.events = result["status"].get("events", [])
                        st.session_state.dataset = result["dataset"]
                        st.session_state.profile = result["profile"]
                        st.success(f"Agent run completed: `{result['job_id']}` — view it on the Intelligence tab.")
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
                st.session_state.job_id = started["job_id"]
                st.session_state.events = []
                st.success(f"Agent run started: `{started['job_id']}` — open Intelligence to watch it live.")
            except Exception as exc:
                st.error(f"Agent run failed: {exc}")
