from __future__ import annotations

import asyncio
import streamlit as st

from ui.components.glass_card import glass_card
from ui.components.chat_bubble import chat_bubble
from ui.components.metric_card import metric_card
from ui.components.feature_selector import feature_selector
from ui.components.plot_3d import pipeline_3d, scatter_3d
from ui.components.feedback import status_badge, agent_node, progress_bar, empty_state, timeline_row
from ui.services.api_client import get_job_status, download_model, run

# ---------------------------------------------------------------------------
# NOTE: st.set_page_config is called in app.py — do NOT call it here.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Design-system CSS (responsive, clean, professional)
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
/* ── Root tokens ── */
:root {
    --bg: #F0FDF4;
    --surface: rgba(240,253,244,0.96);
    --text: #14532D;
    --muted: #64748b;
    --line: rgba(21,128,61,0.15);
    --accent: #15803D;
    --accent-soft: rgba(21,128,61,0.12);
    --success: #22C55E;
    --success-soft: rgba(34,197,94,0.12);
    --warning: #D97706;
    --warning-soft: rgba(217,119,6,0.12);
    --danger: #DC2626;
    --danger-soft: rgba(220,38,38,0.12);
    --radius: 12px;
    --shadow: 0 1px 3px rgba(21,128,61,0.06), 0 1px 2px rgba(21,128,61,0.04);
}

/* ── Global overrides ── */
.stApp { background: var(--bg); }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1400px; }

/* ── Typography ── */
h1 { font-size: 1.75rem !important; font-weight: 700 !important; color: var(--text) !important; letter-spacing: -0.02em; }
h2 { font-size: 1.15rem !important; font-weight: 600 !important; color: var(--text) !important; margin-top: 1.5rem !important; }
h3 { font-size: 1rem !important; font-weight: 600 !important; color: var(--text) !important; }

/* ── Cards ── */
.card {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: var(--radius);
    padding: 20px 24px;
    box-shadow: var(--shadow);
    margin-bottom: 16px;
}

/* ── Metric tile ── */
.metric {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: var(--radius);
    padding: 18px 20px;
    box-shadow: var(--shadow);
    text-align: center;
}
.metric .label { font-size: 0.8rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px; }
.metric .value { font-size: 1.8rem; font-weight: 700; color: var(--text); }
.metric .hint { font-size: 0.75rem; color: var(--muted); margin-top: 4px; }

/* ── Badges ── */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    background: var(--line);
    color: var(--muted);
}
.badge.primary { background: var(--accent-soft); color: var(--accent); }
.badge.success { background: var(--success-soft); color: var(--success); }
.badge.warning { background: var(--warning-soft); color: var(--warning); }
.badge.danger  { background: var(--danger-soft);  color: var(--danger); }

/* ── Pipeline nodes ── */
.node {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 14px; border-radius: 8px; margin-bottom: 6px;
    border: 1px solid var(--line); background: var(--surface);
    font-size: 0.85rem;
}
.node .name { font-weight: 600; color: var(--text); }
.node .state { font-size: 0.72rem; text-transform: uppercase; font-weight: 600; }
.node.completed { border-left: 3px solid var(--success); }
.node.completed .state { color: var(--success); }
.node.failed    { border-left: 3px solid var(--danger); }
.node.failed .state    { color: var(--danger); }
.node.running   { border-left: 3px solid var(--accent); }
.node.running .state   { color: var(--accent); }
.node.queued    { border-left: 3px solid var(--muted); }
.node.queued .state    { color: var(--muted); }

/* ── Chat bubbles ── */
.bubble {
    max-width: 75%; padding: 12px 16px; border-radius: 14px;
    font-size: 0.88rem; line-height: 1.5;
}
.bubble.assistant { background: var(--surface); border: 1px solid var(--line); color: var(--text); }
.bubble.user      { background: var(--accent); color: #fff; }
.bubble .role { font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 4px; opacity: 0.7; }

/* ── Timeline rows ── */
.tl-row {
    padding: 10px 14px; border-radius: 8px; margin-bottom: 6px;
    border: 1px solid var(--line); background: var(--surface);
}
.tl-row .agent { font-weight: 600; color: var(--text); font-size: 0.85rem; }
.tl-row .msg   { font-size: 0.82rem; color: var(--muted); margin-top: 2px; }
.tl-row.completed { border-left: 3px solid var(--success); }
.tl-row.failed    { border-left: 3px solid var(--danger); }

/* ── Empty state ── */
.empty {
    text-align: center; padding: 48px 24px;
    background: var(--surface); border: 1px dashed var(--line);
    border-radius: var(--radius);
}
.empty .icon { font-size: 2.5rem; margin-bottom: 12px; }

/* ── Small muted text ── */
.small-muted { font-size: 0.8rem; color: var(--muted); }

/* ── Responsive tweaks ── */
@media (max-width: 768px) {
    .bubble { max-width: 90%; }
    .metric .value { font-size: 1.4rem; }
    .block-container { max-width: 100%; }
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

def _fetch_job(job_id: str) -> dict | None:
    """Fetch job status from the backend, returning None on failure."""
    try:
        return run(get_job_status(st.session_state.get("api_base_url", ""), job_id))
    except Exception:
        return None


def _fetch_model(job_id: str) -> dict | None:
    """Download the model artifact for a completed job."""
    try:
        return run(download_model(st.session_state.get("api_base_url", ""), job_id))
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Page entry-point
# ---------------------------------------------------------------------------
def intelligence_page() -> None:
    st.title("🧠 Agent Intelligence")

    # ── Sidebar panel ──
    with st.sidebar:
        st.markdown("### ⚙️ Controls")
        job_id = st.text_input("Job ID", placeholder="Paste a job id…", key="job_id_input")

        if job_id:
            job = _fetch_job(job_id)
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
                    model = _fetch_model(job_id)
                    if model and model.get("content"):
                        st.download_button(
                            label="⬇ Download Trained Model",
                            data=model["content"],
                            file_name=model.get("filename", f"{job_id}.joblib"),
                            mime="application/octet-stream",
                            use_container_width=True,
                        )
                    else:
                        st.caption("Model artifact unavailable.")
                else:
                    st.caption("Model available after the run completes.")

    # ── Main area ──
    if not job_id:
        empty_state("🧠", "Enter a Job ID", "Paste a job ID in the sidebar or below to monitor an agent run.")
        job_id = st.text_input("Job ID", placeholder="Paste a job id…", key="job_id_main")
        if not job_id:
            st.stop()

    job = _fetch_job(job_id)
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