'''Module for displaying job intelligence in Streamlit'''

from __future__ import annotations
from typing import Any

import streamlit as st

from ui.components.glass_card import glass_card
from ui.components.metric_card import metric_card
from ui.components.feature_selector import feature_selector
from ui.components.plot_3d import pipeline_3d, scatter_3d
from ui.components.feedback import status_badge, agent_node, progress_bar, empty_state, timeline_row
from ui.services.api_client import get_job_status, download_model, run, create_job

# ---------------------------------------------------------------------------
# NOTE: st.set_page_config is called in app.py — do NOT call it here.
# Dark-theme component styles (inherits global tokens from app.py)
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
/* ── Cards ── */
.card {
    background: rgba(30, 41, 59, 0.6);
    border: 1px solid rgba(148, 163, 184, 0.15);
    border-radius: 12px;
    padding: 20px 24px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    margin-bottom: 16px;
    backdrop-filter: blur(12px);
}

/* ── Metric tile ── */
.metric {
    background: rgba(30, 41, 59, 0.6);
    border: 1px solid rgba(148, 163, 184, 0.15);
    border-radius: 12px;
    padding: 18px 20px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    text-align: center;
    backdrop-filter: blur(12px);
}
.metric .label { font-size: 0.8rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px; }
.metric .value { font-size: 1.8rem; font-weight: 700; color: #f8fafc; }
.metric .hint { font-size: 0.75rem; color: #94a3b8; margin-top: 4px; }

/* ── Badges ── */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    background: rgba(148, 163, 184, 0.15);
    color: #94a3b8;
}
.badge.primary { background: rgba(37, 99, 235, 0.2); color: #60a5fa; }
.badge.success { background: rgba(34, 197, 94, 0.15); color: #4ade80; }
.badge.warning { background: rgba(217, 119, 6, 0.15); color: #fbbf24; }
.badge.danger  { background: rgba(220, 38, 38, 0.15);  color: #f87171; }

/* ── Pipeline nodes ── */
.node {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 14px; border-radius: 8px; margin-bottom: 6px;
    border: 1px solid rgba(148, 163, 184, 0.15); background: rgba(30, 41, 59, 0.6);
    font-size: 0.85rem;
}
.node .name { font-weight: 600; color: #f8fafc; }
.node .state { font-size: 0.72rem; text-transform: uppercase; font-weight: 600; }
.node.completed { border-left: 3px solid #4ade80; }
.node.completed .state { color: #4ade80; }
.node.failed    { border-left: 3px solid #f87171; }
.node.failed .state    { color: #f87171; }
.node.running   { border-left: 3px solid #60a5fa; }
.node.running .state   { color: #60a5fa; }
.node.queued    { border-left: 3px solid #94a3b8; }
.node.queued .state    { color: #94a3b8; }

/* ── Chat bubbles ── */
.bubble {
    max-width: 75%; padding: 12px 16px; border-radius: 14px;
    font-size: 0.88rem; line-height: 1.5;
}
.bubble.assistant { background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(148, 163, 184, 0.15); color: #f8fafc; }
.bubble.user      { background: #2563eb; color: #fff; }
.bubble .role { font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 4px; opacity: 0.7; }

/* ── Timeline rows ── */
.tl-row {
    padding: 10px 14px; border-radius: 8px; margin-bottom: 6px;
    border: 1px solid rgba(148, 163, 184, 0.15); background: rgba(30, 41, 59, 0.6);
}
.tl-row .agent { font-weight: 600; color: #f8fafc; font-size: 0.85rem; }
.tl-row .msg   { font-size: 0.82rem; color: #94a3b8; margin-top: 2px; }
.tl-row.completed { border-left: 3px solid #4ade80; }
.tl-row.failed    { border-left: 3px solid #f87171; }

/* ── Empty state ── */
.empty {
    text-align: center; padding: 48px 24px;
    background: rgba(30, 41, 59, 0.4); border: 1px dashed rgba(148, 163, 184, 0.3);
    border-radius: 12px;
}
.empty .icon { font-size: 2.5rem; margin-bottom: 12px; }

/* ── Small muted text ── */
.small-muted { font-size: 0.8rem; color: #94a3b8; }

/* ── Responsive tweaks ── */
@media (max-width: 768px) {
    .bubble { max-width: 90%; }
    .metric .value { font-size: 1.4rem; }
}
@media (max-width: 480px) {
    .bubble { max-width: 95%; font-size: 0.82rem; }
    .metric .value { font-size: 1.2rem; }
    .tl-row { padding: 8px 10px; }
    .empty { padding: 32px 16px; }
}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fetch_job(job_id: str) -> dict[str, Any] | None:
    """Fetch job status from the backend, returning None on failure."""
    try:
        return run(get_job_status(st.session_state.get("api_base_url", ""), job_id))
    except Exception:
        return None


def _fetch_model(job_id: str) -> dict[str, Any] | None:
    """Download the model artifact for a completed job."""
    try:
        return run(download_model(st.session_state.get("api_base_url", ""), job_id))
    except Exception:
        return None

def intelligence_page() -> None:
    st.title("🧠 Agent Intelligence")

    # ── Sidebar panel ──
    with st.sidebar:
        st.markdown("### ⚙️ Controls")
    # Use existing session state to pre‑populate the input
    job_id_input = st.text_input("Job ID", value=st.session_state.get("job_id_input", ""), key="job_id_input")
    if st.button("Create Job", key="create_job_btn"):
        # Create a new job and populate the input field
        try:
            result = run(create_job(st.session_state.get("api_base_url", "")))
            new_job_id = result.get("job_id")
            st.session_state["job_id_input"] = new_job_id
            st.success("Job created: " + new_job_id)
        except Exception as e:
            st.error(f"Failed to create job: {e}")
        if job_id_input:
            job = _fetch_job(job_id_input)
            if job is None:
                empty_state("🔍", "Job Not Found", "Double-check the Job ID and try again.")
            else:
                status = job.get("status", "unknown")
                kind_map = {"completed": "success", "running": "primary", "failed": "danger", "queued": ""}
                status_badge(status.upper(), kind_map.get(status, ""))

                completed = job.get("completed_stages", 0)
                total = job.get("total_stages", len(job.get("stages", [])) or 9)
                progress_bar(completed, total)

                st.markdown("---")
                st.markdown("### 📥 Model")
                if status == "completed":
                    model = _fetch_model(job_id_input)
                    if model and model.get("content"):
                        st.download_button(
                            label="⬇ Download Trained Model",
                            data=model["content"],
                            file_name=model.get("filename", f"{job_id_input}.joblib"),
                            mime="application/octet-stream",
                            use_container_width=True,
                        )
                    else:
                        st.caption("Model artifact unavailable.")
                else:
                    st.caption("Model available after the run completes.")

    # ── Main area ──
    if not job_id_input:
        empty_state("🧠", "Enter a Job ID", "Paste a job ID in the sidebar or below to monitor an agent run.")
        job_id = st.text_input("Job ID", placeholder="Paste a job id…", key="job_id_main")
        if not job_id:
            st.stop()

    job = _fetch_job(job_id_input or st.session_state.get("job_id_main", ""))
    if job is None:
        empty_state("❌", "Job not found", "The job ID you entered does not match any known run.")
        st.stop()

    # Type narrowed — job is guaranteed dict from here
    assert job is not None

    # ── Pipeline stages ──
    stages = job.get("stages", [])
    if stages:
        st.subheader("🔁 Agent Pipeline")
        cols = st.columns(min(len(stages), 5))
        for i, s in enumerate(stages):
            with cols[i % 5]:
                agent_node(s.get("name", f"Stage {i+1}"), s.get("status", "queued"))

        # 3D spiral view
        with st.expander("🌐 3D Pipeline View", expanded=False):
            pipeline_3d(stages, height=420)

    # ── Metrics row ──
    metrics = job.get("metrics", {})
    if metrics:
        st.subheader("📊 Performance Metrics")
        metric_cols = st.columns(len(metrics))
        for col, (label, value) in zip(metric_cols, metrics.items()):
            with col:
                metric_card(label, value)

    # ── Feature importance ──
    features = job.get("features", [])
    if features:
        st.subheader("🔬 Feature Importance")
        selected = feature_selector(features, job.get("target"))
        if selected:
            st.caption(f"{len(selected)} feature{'s' if len(selected) != 1 else ''} selected for the model.")

    # ── Timeline ──
    timeline = job.get("timeline", [])
    if timeline:
        st.subheader("📋 Reasoning Timeline")
        for entry in timeline:
            timeline_row(
                entry.get("agent", "Agent"),
                entry.get("message", ""),
                entry.get("status", "completed"),
            )

    # ── Insights ──
    insights = job.get("insights", [])
    if insights:
        st.subheader("💡 Insights")
        for insight in insights:
            glass_card(insight.get("title", "Insight"), insight.get("body", ""))

    # ── 3D Embedding view ──
    embedding_points = job.get("embedding_points")
    if embedding_points:
        with st.expander("🧬 3D Data Embeddings", expanded=False):
            scatter_3d(embedding_points, height=460, title="Dataset Embedding Space")


if __name__ == "__main__":
    intelligence_page()