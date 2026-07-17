from __future__ import annotations

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

    # ---- Sync events (WebSocket when available, REST fallback) ----------
    if not st.session_state.serverless:
        event_client.start(st.session_state.ws_base_url, job_id)
        ws_events = event_client.drain()
        if ws_events:
            append_events(ws_events)

    try:
        job_status = api_client.run(api_client.get_job_status(st.session_state.api_base_url, job_id))
        backend_events = job_status.get("events", [])
        if backend_events:
            seen_ids = {e["id"] for e in st.session_state.events}
            new_events = [e for e in backend_events if e["id"] not in seen_ids]
            if new_events:
                append_events(new_events)
    except Exception as exc:
        st.warning(f"Unable to sync job status from backend: {exc}") # type: ignore

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
    st.subheader("Experiment tracking")
    try:
        experiments = api_client.list_experiments(st.session_state.api_base_url)["experiments"]
        st.session_state.last_experiments = experiments
    except httpx.HTTPStatusError as exc:
        st.warning(f"Experiment store unavailable: {exc}")
        experiments = st.session_state.last_experiments

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
        try:
            job_status = api_client.run(api_client.get_job_status(st.session_state.api_base_url, job_id))
            exp = job_status.get("experiment") or {}
        except httpx.HTTPStatusError:
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

    # ---- Model export --------------------------------------------------
    if job_state == "completed":
        st.markdown('<hr class="soft">', unsafe_allow_html=True)
        st.subheader("Deploy model")
        st.caption("Download the trained, deployable pipeline artifact (joblib).")
        try:
            artifact = api_client.run(api_client.download_model(st.session_state.api_base_url, job_id))
            st.download_button(
                "⬇ Download model artifact",
                data=artifact["content"],
                file_name=artifact["filename"],
                mime="application/octet-stream",
                width="stretch",
                type="primary",
            ) # type: ignore
        except httpx.HTTPStatusError as exc:
            st.error(f"Model export unavailable: {exc}")


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
