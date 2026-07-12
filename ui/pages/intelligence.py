from __future__ import annotations

import pandas as pd
import streamlit as st

from ui.components.feedback import agent_node, empty_state, progress_bar, timeline_row
from ui.components.metric_card import metric_card
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
        st.warning(f"Unable to sync job status from backend: {exc}")

    events = st.session_state.events
    status_by_agent = _status_by_agent(events)
    completed = sum(1 for agent in PIPELINE if status_by_agent.get(agent) == "completed")
    job_state = _job_status(events)

    # ---- Header metrics ------------------------------------------------
    cols = st.columns(4)
    with cols[0]:
        metric_card("Job", job_id[:8], "Execution trace", accent="#4cc9f0")
    with cols[1]:
        metric_card("Progress", f"{completed}/{len(PIPELINE)}", "Agent stages", accent="#7bd88f")
    with cols[2]:
        metric_card("Events", len(events), "Replay cache", accent="#f6c177")
    with cols[3]:
        accent = {"completed": "#7bd88f", "failed": "#ff6b6b", "running": "#4cc9f0"}.get(job_state, "#91a0b8")
        metric_card("Status", job_state.capitalize(), "Runtime state", accent=accent)

    progress_bar(completed, len(PIPELINE))

    # ---- Two-column layout --------------------------------------------
    left, right = st.columns([1.1, 1])
    with left:
        st.subheader("Execution graph")
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
    except Exception as exc:
        st.warning(f"Experiment store unavailable: {exc}")
        experiments = st.session_state.last_experiments

    if experiments:
        df = pd.DataFrame(experiments)
        if "metrics" in df.columns:
            df = df.drop(columns=["metrics"])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.caption("No completed experiments yet.")


def _status_by_agent(events: list[dict]) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for event in events:
        agent = event.get("agent")
        if agent:
            statuses[agent] = event.get("status", "running")
    return statuses


def _job_status(events: list[dict]) -> str:
    for event in reversed(events):
        if event.get("type") == "job_status":
            return event.get("status", "running")
    return "running"
