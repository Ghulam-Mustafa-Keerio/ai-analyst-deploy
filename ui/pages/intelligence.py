from __future__ import annotations

import logging
from typing import Any
import httpx

import pandas as pd
import streamlit as st

from ui.components.feedback import agent_node, empty_state, progress_bar, timeline_row
from ui.components.metric_card import metric_card
from ui.components.plot_3d import experiments_3d, pipeline_3d, metrics_3d, feature_importance_3d
from ui.services import api_client
from ui.services.ws_client import event_client
from ui.state.app_state import append_events

logger = logging.getLogger(__name__)


PIPELINE = [
    "PlannerAgent",
    "DataProfilerAgent",
    "DataQualityAgent",
    "FeatureSelectionAgent",
    "ModelDebateAgent",
    "ModelSelectionAgent",
    "TrainingAgent",
    "EvaluationAgent",
    "InsightGenerationAgent",
]


def render_intelligence() -> None:
    st.markdown('<div class="eyebrow">Workspace / Intelligence</div>', unsafe_allow_html=True)
    st.title("Live Intelligence")
    job_id = st.session_state.job_id
    if not job_id:
        empty_state(
            "🧠",
            "No active agent run",
            "Start an agent run from the Dashboard to open the live reasoning console.",
        )
        return

    st.session_state.setdefault("last_experiments", [])

    # ---- Sync events (WebSocket for live, REST for catch-up) ----------
    # [+] Bug Fix: The WebSocket client was imported but never called, breaking live updates.
    # This re-enables the live event stream for self-hosted runs.
    if not st.session_state.serverless:
        event_client(st.session_state.api_base_url, job_id)

    job_status = None
    try:
        # The REST endpoint serves as a catch-up mechanism on page load/refresh
        job_status = api_client.run(api_client.get_job_status(st.session_state.api_base_url, job_id))
        backend_events = job_status.get("events", [])
        if backend_events:
            seen_ids = {e.get("id") for e in st.session_state.get("events", [])}
            new_events = [e for e in backend_events if e.get("id") not in seen_ids]
            if new_events:
                append_events(new_events)
    except httpx.HTTPError as exc:
        # [+] UX/Reliability: Instead of silently failing, inform the user about sync issues
        # with a non-disruptive toast, and log the error for debugging.
        logger.warning(f"Unable to sync job status from backend: {exc}", exc_info=True)
        st.toast(f"⚠️ Sync failed: {exc}", icon="🔥")

    job_state = _job_status(st.session_state.get("events", []))

    events = st.session_state.events
    status_by_agent = _status_by_agent(events)
    completed = sum(1 for agent in PIPELINE if status_by_agent.get(agent) == "completed")
    job_state = _job_status(events)

    # ---- Header metrics ------------------------------------------------
    cols = st.columns(4)
    with cols[0]:
        metric_card("Job", job_id[:8], "Execution trace", accent="#2563eb")
    with cols[1]:
        metric_card("Progress", f"{completed}/{len(PIPELINE)}", "Agent stages", accent="#16a34a")
    with cols[2]:
        metric_card("Events", len(events), "Replay cache", accent="#d97706")
    with cols[3]:
        accent = {"completed": "#16a34a", "failed": "#dc2626", "running": "#2563eb"}.get(job_state, "#64748b")
        metric_card("Status", job_state.capitalize(), "Runtime state", accent=accent)

    progress_bar(completed, len(PIPELINE))

    # ---- Two-column layout --------------------------------------------
    left, right = st.columns([1.1, 1])
    with left:
        st.subheader("Execution graph")
        with st.expander("3D pipeline view", expanded=True):
            stages = [
                {"name": agent, "status": status_by_agent.get(agent, "queued")} for agent in PIPELINE
            ]
            pipeline_3d(stages)
        st.caption("Linear list")
        for agent in PIPELINE:
            agent_node(agent, status_by_agent.get(agent, "queued"))

    with right:
        st.subheader("Reasoning timeline")
        if events:
            for event in reversed(events):
                agent = event.get("agent") or "Runtime"
                timeline_row(agent, event.get("message", ""), event.get("status", "running"))
        else:
            st.caption("Awaiting first events…")

    # ---- Experiment tracking ------------------------------------------
    st.markdown('<hr class="soft">', unsafe_allow_html=True)
    st.subheader("Experiment Tracking")
    try:
        # [+] Data Consistency: Use the cached `list_experiments` for a general overview,
        # but ensure the final experiment from the *current* completed job is always included
        # by pulling it directly from the uncached `get_job_status` result.
        experiments = api_client.run(api_client.list_experiments(st.session_state.api_base_url))["experiments"]
        st.session_state.last_experiments = experiments
    except httpx.HTTPStatusError as exc:
        st.warning(f"Experiment store unavailable: {exc}")
        experiments = st.session_state.last_experiments
    
    if job_state == "completed" and job_status:
        final_experiment = job_status.get("experiment")
        _ensure_experiment_in_list(experiments, final_experiment)

    if experiments:
        df = pd.DataFrame(experiments)
        if "metrics" in df.columns:
            df = df.drop(columns=["metrics"])
        st.dataframe(df, width="stretch", hide_index=True)

        with st.expander("3D experiment space", expanded=False):
            st.caption("Each experiment placed by accuracy / F1 / train time.")
            experiments_3d(experiments)
    else:
        st.caption("No completed experiments yet.")

    # ---- 3D model quality & feature importance ------------------------
    if job_state == "completed":
        _render_completed_job_artifacts(job_id)


def _status_by_agent(events: list[dict[str, Any]]) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for event in events:
        agent = event.get("agent")
        if agent:
            statuses[agent] = event.get("status", "running")
    return statuses


def _job_status(events: list[dict[str, Any]]) -> str:
    for event in reversed(events):
        if event.get("type") == "job_status":
            return event.get("status", "running")
    return "running"


def _ensure_experiment_in_list(experiments: list[dict[str, Any]], new_experiment: dict[str, Any] | None) -> None:
    """Ensure the given experiment is in the list, replacing it by ID if a stale version exists."""
    if not new_experiment or not new_experiment.get("experiment_id"):
        return

    exp_id_to_add = new_experiment["experiment_id"]
    # [+] Data Consistency Bug Fix: The previous implementation only added the experiment if it
    # was missing, but didn't update it if a stale version was in the cache.
    # This new logic finds and replaces the stale entry, ensuring data is always fresh.
    for i, existing_exp in enumerate(experiments):
        if existing_exp.get("experiment_id") == exp_id_to_add:
            experiments[i] = new_experiment  # Replace stale entry
            return
    experiments.insert(0, new_experiment)  # Or add if not found


def _render_completed_job_artifacts(job_id: str) -> None:
    """Fetch and render artifacts for a completed job, like metrics and model downloads."""
    st.markdown('<hr class="soft">', unsafe_allow_html=True)
    st.subheader("Completed Run Artifacts")

    try:
        job_status = api_client.run(api_client.get_job_status(st.session_state.api_base_url, job_id))
        exp = job_status.get("experiment") or {}
    except httpx.HTTPStatusError as exc:
        st.warning(f"Could not load final job status: {exc}")
        exp = {}

    metrics = exp.get("metrics") or {}
    feat_imp = exp.get("feature_importance") or []
    if isinstance(feat_imp, list):
        feat_imp = {fi.get("feature"): float(fi.get("importance", 0.0)) for fi in feat_imp if isinstance(fi, dict)}

    if metrics:
        with st.expander("📊 3D metrics globe", expanded=False):
            st.caption("Each metric is a vertex; radial distance encodes its normalised score.")
            metrics_3d(metrics)
    if feat_imp:
        with st.expander("🧬 3D feature importance", expanded=False):
            st.caption("Features wrapped on a helix; radius encodes normalised importance.")
            feature_importance_3d(feat_imp)

    st.subheader("Deploy model")
    st.caption("Download the trained, deployable pipeline artifact (joblib).")
    try:
        artifact = api_client.run(api_client.download_model(st.session_state.api_base_url, job_id))
        st.download_button(
            "⬇ Download model artifact",
            data=artifact["content"],
            file_name=artifact["filename"],
            mime="application/octet-stream",
            use_container_width=True,
            type="primary",
        )
    except httpx.HTTPStatusError as exc:
        st.error(f"Model export unavailable: {exc}")
