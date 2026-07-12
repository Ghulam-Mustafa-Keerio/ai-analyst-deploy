from __future__ import annotations

import pandas as pd
import streamlit as st

from ui.components.feature_selector import feature_selector
from ui.components.metric_card import metric_card
from ui.services import api_client


def render_dashboard() -> None:
    st.markdown("<div class='agent-shell'>", unsafe_allow_html=True)
    st.title("Autonomous Data Science Agent OS")
    st.caption("Upload a dataset, select autonomy boundaries, and launch an observable agent pipeline.")

    uploaded = st.file_uploader("Dataset", type=["csv", "parquet"])
    if uploaded and st.button("Upload dataset", use_container_width=True):
        result = api_client.run(
            api_client.upload_dataset(st.session_state.api_base_url, uploaded.name, uploaded.getvalue())
        )
        st.session_state.dataset = result["dataset"]
        st.session_state.profile = result["profile"]
        st.session_state.events = []
        st.success("Dataset registered.")

    dataset = st.session_state.dataset
    profile = st.session_state.profile
    if not dataset or not profile:
        st.info("Load a CSV or Parquet dataset to initialize lineage and agent controls.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    cols = st.columns(4)
    with cols[0]:
        metric_card("Rows", f"{dataset['rows']:,}", "Registered in dataset memory")
    with cols[1]:
        metric_card("Columns", dataset["columns"], "Schema inferred")
    with cols[2]:
        metric_card("Dataset ID", dataset["dataset_id"][:8], "Lineage key")
    with cols[3]:
        metric_card("Mode", "Autonomous", "Default control level")

    st.subheader("Dataset Lineage & Domain Analysis")
    col_lineage, col_domain = st.columns([1.2, 1])
    with col_lineage:
        st.markdown(
            f"""
            <div class="glass-card" style="min-height: 95px;">
                <div class="metric-label">Dataset File</div>
                <b>{dataset['filename']}</b>
                <div class="small-muted">{dataset['path']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_domain:
        detected = profile.get("domain", {})
        domain_name = detected.get("domain", "general")
        domain_conf = detected.get("confidence", 0.0)
        st.markdown(
            f"""
            <div class="glass-card" style="min-height: 95px;">
                <div class="metric-label">Detected Business Domain</div>
                <b style="color: var(--blue); text-transform: uppercase;">{domain_name}</b>
                <div class="small-muted">Confidence: {domain_conf:.1%}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if domain_name and domain_name != "general":
        with st.expander(f"📖 Business Domain Reference Guidelines: {domain_name.upper()}", expanded=False):
            try:
                domain_info = api_client.run(
                    api_client.get_domain_details(st.session_state.api_base_url, domain_name)
                )
                st.markdown(domain_info["content"])
            except Exception as exc:
                st.info(f"Domain reference content loaded from backend: {exc}")

    with st.expander("Schema", expanded=False):
        schema_df = pd.DataFrame(
            [{"column": column, "dtype": dtype, "missing_ratio": profile["missing_ratio"].get(column, 0)} for column, dtype in dataset["schema"].items()]
        )
        st.dataframe(schema_df, use_container_width=True, hide_index=True)

    with st.expander("Data Preview (First 50 Rows)", expanded=False):
        try:
            preview_data = api_client.run(
                api_client.preview_dataset(st.session_state.api_base_url, dataset["dataset_id"], page=1, page_size=50)
            )
            preview_df = pd.DataFrame(preview_data["rows"])
            st.dataframe(preview_df, use_container_width=True)
        except Exception as exc:
            st.warning(f"Unable to load dataset preview: {exc}")

    st.subheader("Launch Pipeline")
    columns = list(dataset["schema"])
    mode = st.segmented_control("Autonomy", ["manual", "assisted", "autonomous"], default="autonomous")
    target = st.selectbox("Target", columns, index=max(len(columns) - 1, 0))
    model = None
    features: list[str] = []
    if mode == "manual":
        model = st.selectbox("Model", ["linear", "random_forest"])
        features = feature_selector(columns, target)
    elif mode == "assisted":
        features = feature_selector(columns, target)

    if st.button("Start agent run", type="primary", use_container_width=True):
        if st.session_state.serverless:
            # Serverless backends run the pipeline inline and return the full
            # result in a single request (no persistent state between calls).
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
            st.success(f"Agent run completed: {result['job_id']}")
        else:
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
            st.success(f"Agent run started: {started['job_id']}")

    st.markdown("</div>", unsafe_allow_html=True)
