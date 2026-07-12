from __future__ import annotations

import pandas as pd
import streamlit as st

from ui.components.feedback import empty_state
from ui.components.feature_selector import feature_selector
from ui.components.metric_card import metric_card
from ui.services import api_client


def render_dashboard() -> None:
    st.markdown('<div class="eyebrow">Workspace / Dashboard</div>', unsafe_allow_html=True)
    st.title("Autonomous Data Science Agent OS")
    st.caption(
        "Upload a dataset, set autonomy boundaries, and launch an observable multi-agent pipeline."
    )

    st.markdown('<hr class="soft">', unsafe_allow_html=True)

    # ---- Upload ----------------------------------------------------------
    st.subheader("1 · Ingest dataset")
    uploaded = st.file_uploader(
        "Dataset",
        type=["csv", "parquet"],
        help="CSV or Parquet. Stored in dataset memory and profiled for schema + business domain.",
    )
    if uploaded and st.button("Register dataset", use_container_width=True, type="primary"):
        with st.spinner("Profiling dataset & detecting domain…"):
            try:
                result = api_client.run(
                    api_client.upload_dataset(
                        st.session_state.api_base_url, uploaded.name, uploaded.getvalue()
                    )
                )
                st.session_state.dataset = result["dataset"]
                st.session_state.profile = result["profile"]
                st.session_state.events = []
                st.session_state.job_id = None
                st.success(f"Registered `{uploaded.name}` ({result['dataset']['rows']:,} rows).")
            except Exception as exc:
                st.error(f"Upload failed: {exc}")

    dataset = st.session_state.dataset
    profile = st.session_state.profile

    if not dataset or not profile:
        st.markdown('<hr class="soft">', unsafe_allow_html=True)
        empty_state(
            "📂",
            "No dataset loaded",
            "Upload a CSV or Parquet file above to initialise lineage, schema profiling, and domain analysis.",
        )
        return

    # ---- Lineage & domain ---------------------------------------------
    st.markdown('<hr class="soft">', unsafe_allow_html=True)
    st.subheader("2 · Dataset lineage & domain")

    cols = st.columns(4)
    with cols[0]:
        metric_card("Rows", f"{dataset['rows']:,}", "Registered in dataset memory", accent="#4cc9f0")
    with cols[1]:
        metric_card("Columns", dataset["columns"], "Schema inferred", accent="#4cc9f0")
    with cols[2]:
        metric_card("Dataset ID", dataset["dataset_id"][:8], "Lineage key", accent="#7bd88f")
    with cols[3]:
        metric_card("Mode", "Autonomous", "Default control level", accent="#f6c177")

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
        st.dataframe(schema_df, use_container_width=True, hide_index=True)

        try:
            preview_data = api_client.run(
                api_client.preview_dataset(st.session_state.api_base_url, dataset["dataset_id"], page=1, page_size=50)
            )
            preview_df = pd.DataFrame(preview_data["rows"])
            st.dataframe(preview_df, use_container_width=True, hide_index=True)
        except Exception as exc:
            st.warning(f"Unable to load preview: {exc}")

    # ---- Launch ----------------------------------------------------------
    st.markdown('<hr class="soft">', unsafe_allow_html=True)
    st.subheader("3 · Launch agent pipeline")

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

    if st.button("Start agent run", type="primary", use_container_width=True):
        if st.session_state.serverless:
            with st.spinner("Running agent pipeline (serverless)…"):
                try:
                    result = api_client.run(
                        api_client.run_agent(
                            st.session_state.api_base_url,
                            filename=dataset["filename"],
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
