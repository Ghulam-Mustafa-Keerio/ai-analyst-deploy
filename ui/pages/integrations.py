"""Integrations page: MCP tools, experiment tracking, knowledge graph, BI connectors."""

from __future__ import annotations

import streamlit as st

st.markdown(
    """
<style>
/* ── Integrations page dark theme ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: rgba(30, 41, 59, 0.4);
    border-radius: 12px;
    padding: 6px;
    border: 1px solid rgba(148, 163, 184, 0.15);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 0.85rem;
    font-weight: 500;
    color: #94a3b8;
    transition: all 0.2s ease;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #f8fafc;
    background: rgba(148, 163, 184, 0.1);
}
.stTabs [aria-selected="true"] {
    background: rgba(37, 99, 235, 0.15) !important;
    color: #60a5fa !important;
}
.stTabs [data-baseweb="tab-highlight"] {
    background-color: #2563eb !important;
}
.stTabs [data-baseweb="tab-border"] {
    display: none;
}

/* ── Expander dark theme ── */
.streamlit-expander {
    background: rgba(30, 41, 59, 0.4) !important;
    border: 1px solid rgba(148, 163, 184, 0.15) !important;
    border-radius: 12px !important;
    overflow: hidden;
}
.streamlit-expander > details > summary {
    color: #f8fafc !important;
    font-weight: 600;
}

/* ── Section headers ── */
.integration-section h3 {
    color: #f8fafc !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
}

/* ── Soft hr ── */
hr.soft {
    border: none;
    border-top: 1px solid rgba(148, 163, 184, 0.15);
    margin: 1.5rem 0;
}
</style>
""",
    unsafe_allow_html=True,
)


def _api(method: str, path: str, **kwargs):
    """Helper to call the backend API."""
    import httpx

    base = st.session_state.get("api_base_url", "http://localhost:8000")
    try:
        with httpx.Client(timeout=30) as client:
            resp = client.request(method, f"{base}{path}", **kwargs)
            if resp.status_code >= 400:
                return None, f"HTTP {resp.status_code}: {resp.text}"
            return resp.json(), None
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)


def render_integrations() -> None:
    st.markdown('<div class="eyebrow">Platform Extensions</div>', unsafe_allow_html=True)
    st.markdown("## 🔌 Integrations & MLOps")
    st.caption("Manage MCP tools, experiment tracking, knowledge graphs, and BI connectors.")
    st.markdown('<hr class="soft">', unsafe_allow_html=True)

    tab_mcp, tab_track, tab_graph, tab_bi = st.tabs(
        ["🛠️ MCP Tools", "📊 Experiment Tracking", "🕸️ Knowledge Graph", "📈 BI Connectors"]
    )

    # ── MCP Tools ──────────────────────────────────────────────────────────
    with tab_mcp:
        st.markdown("### Model Context Protocol")
        st.caption("Discover and invoke tools exposed by MCP servers.")
        if st.button("🔄 Discover MCP Tools", key="mcp_discover", use_container_width=True):
            with st.spinner("Discovering…"):
                data, err = _api("GET", "/mcp/tools")
            if err:
                st.error(err)
            else:
                servers = data.get("servers", [])
                tools = data.get("tools", [])
                st.success(f"Found {len(tools)} tools across {len(servers)} servers.")
                if tools:
                    st.dataframe(tools, use_container_width=True, hide_index=True)
                else:
                    st.info("No MCP tools discovered. Configure MCP servers via environment variables.")

        st.markdown("---")
        with st.expander("🔧 Call a Tool"):
            tool_name = st.text_input("Tool name", key="mcp_tool_name")
            tool_args = st.text_area("Arguments (JSON)", value="{}", key="mcp_tool_args")
            if st.button("Invoke", key="mcp_invoke", type="primary"):
                import json

                try:
                    args = json.loads(tool_args)
                except json.JSONDecodeError as exc:
                    st.error(f"Invalid JSON: {exc}")
                else:
                    data, err = _api("POST", "/mcp/call", json={"tool_name": tool_name, "arguments": args})
                    if err:
                        st.error(err)
                    else:
                        st.json(data)

    # ── Experiment Tracking ────────────────────────────────────────────────
    with tab_track:
        st.markdown("### Experiment Tracking")
        st.caption("Track agent runs in MLflow, Weights & Biases, or in-memory store.")
        jobs = st.session_state.get("jobs", {})
        if jobs:
            options = {jid: f"{jid[:8]}… ({meta.get('dataset_id', '?')})" for jid, meta in jobs.items()}
            selected = st.selectbox("Select job", list(options.keys()), format_func=lambda j: options.get(j, j))
            if st.button("📊 Track Experiment", key="track_btn", use_container_width=True):
                with st.spinner("Tracking…"):
                    data, err = _api("POST", "/tracking/track", json={"job_id": selected})
                if err:
                    st.error(err)
                else:
                    st.success(f"Tracked! Run ID: `{data.get('run_id', '?')}` | Backend: {data.get('backend', '?')}")
                    st.json(data)
        else:
            st.info("No jobs available. Run an agent first from the Dashboard.")

        st.markdown("---")
        if st.button("📋 List Tracked Runs", key="track_list", use_container_width=True):
            data, err = _api("GET", "/tracking/runs")
            if err:
                st.error(err)
            else:
                runs = data.get("runs", [])
                if runs:
                    st.dataframe(runs, use_container_width=True, hide_index=True)
                else:
                    st.info("No tracked runs yet.")

    # ── Knowledge Graph ───────────────────────────────────────────────────
    with tab_graph:
        st.markdown("### Knowledge Graph")
        st.caption("Build a knowledge graph from a dataset to explore column relationships.")
        jobs = st.session_state.get("jobs", {})
        if jobs:
            ds_options = {jid: meta.get("dataset_id", jid[:8]) for jid, meta in jobs.items()}
            ds_selected = st.selectbox("Select job (for dataset)", list(ds_options.keys()), format_func=lambda j: ds_options.get(j, j))
            col1, col2 = st.columns(2)
            with col1:
                corr_thresh = st.slider("Correlation threshold", 0.0, 1.0, 0.7, 0.05)
            with col2:
                max_entities = st.number_input("Max categorical entities", 10, 200, 50, step=10)
            if st.button("🕸️ Build Graph", key="graph_build", type="primary", use_container_width=True):
                with st.spinner("Building knowledge graph…"):
                    data, err = _api(
                        "POST",
                        "/graph/build",
                        json={
                            "dataset_id": ds_options[ds_selected],
                            "correlation_threshold": corr_thresh,
                            "max_categorical_entities": int(max_entities),
                        },
                    )
                if err:
                    st.error(err)
                else:
                    nodes = data.get("nodes", [])
                    edges = data.get("edges", [])
                    st.success(f"Graph built: {len(nodes)} nodes, {len(edges)} edges.")
                    st.json(data)
        else:
            st.info("No datasets available. Run an agent first from the Dashboard.")

    # ── BI Connectors ─────────────────────────────────────────────────────
    with tab_bi:
        st.markdown("### BI Connectors")
        st.caption("Push results to Power BI or run dbt transformations.")

        with st.expander("🔴 Power BI"):
            st.markdown("Push dataset rows to a Power BI push dataset.")
            pbi_dataset = st.text_input("Dataset ID (Power BI)", key="pbi_dataset_id")
            pbi_table = st.text_input("Table name", key="pbi_table")
            pbi_rows_json = st.text_area("Rows (JSON array)", value="[]", key="pbi_rows")
            if st.button("Push to Power BI", key="pbi_push_btn"):
                import json

                try:
                    rows = json.loads(pbi_rows_json)
                except json.JSONDecodeError as exc:
                    st.error(f"Invalid JSON: {exc}")
                else:
                    data, err = _api(
                        "POST",
                        "/bi/pbi/push",
                        json={"dataset_id": pbi_dataset, "table_name": pbi_table, "rows": rows},
                    )
                    if err:
                        st.error(err)
                    else:
                        st.success("Rows pushed to Power BI.")
                        st.json(data)

        with st.expander("🟠 dbt"):
            st.markdown("Run a dbt transformation pipeline.")
            dbt_project = st.text_input("Project directory", value=".", key="dbt_project")
            dbt_cloud = st.checkbox("Use dbt Cloud", key="dbt_cloud")
            if st.button("Run dbt", key="dbt_run_btn"):
                payload = {"project_dir": dbt_project, "use_cloud": dbt_cloud}
                data, err = _api("POST", "/bi/dbt/run", json=payload)
                if err:
                    st.error(err)
                else:
                    st.success("dbt run completed.")
                    st.json(data)
