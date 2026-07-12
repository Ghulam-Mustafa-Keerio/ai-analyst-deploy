from __future__ import annotations

import html
import json

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

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
    st.title("Live Intelligence")
    job_id = st.session_state.job_id
    if not job_id:
        st.info("Start an agent run from the Dashboard to open the live reasoning console.")
        return

    if not st.session_state.serverless:
        event_client.start(st.session_state.ws_base_url, job_id)
        ws_events = event_client.drain()
        if ws_events:
            append_events(ws_events)

    # HTTP Fallback & Sync:
    # Query the job status via REST to ensure we have the complete and final set of events,
    # especially in serverless or blocked WebSocket environments.
    try:
        job_status = api_client.run(api_client.get_job_status(st.session_state.api_base_url, job_id))
        backend_events = job_status.get("events", [])
        if backend_events:
            # Reconcile events in session state by ID to prevent duplicates
            seen_ids = {e["id"] for e in st.session_state.events}
            new_events = [e for e in backend_events if e["id"] not in seen_ids]
            if new_events:
                append_events(new_events)
    except Exception as exc:
        st.warning(f"Unable to sync job status from backend: {exc}")

    events = st.session_state.events
    status_by_agent = _status_by_agent(events)
    completed = sum(1 for agent in PIPELINE if status_by_agent.get(agent) == "completed")

    cols = st.columns(4)
    with cols[0]:
        metric_card("Job", job_id[:8], "Execution trace")
    with cols[1]:
        metric_card("Progress", f"{completed}/{len(PIPELINE)}", "Agent stages")
    with cols[2]:
        metric_card("Events", len(events), "Replay cache")
    with cols[3]:
        metric_card("Status", _job_status(events), "Runtime state")

    left, right = st.columns([1.1, 1])
    with left:
        st.subheader("Execution Graph")
        for agent in PIPELINE:
            status = status_by_agent.get(agent, "queued")
            st.markdown(
                f"<div class='agent-node {status}'><b>{agent}</b><br><span class='small-muted'>{status}</span></div>",
                unsafe_allow_html=True,
            )

    with right:
        st.subheader("Reasoning Timeline")
        _browser_websocket_timeline(st.session_state.api_base_url, st.session_state.ws_base_url, job_id)
        if events:
            with st.expander("Python event cache", expanded=False):
                for event in reversed(events[-15:]):
                    st.json(event)

    st.subheader("Experiment Tracking")
    try:
        experiments = api_client.list_experiments(st.session_state.api_base_url)["experiments"]
        st.session_state.last_experiments = experiments
    except Exception as exc:
        st.warning(f"Experiment store unavailable: {exc}")
        experiments = st.session_state.last_experiments

    if experiments:
        st.dataframe(pd.DataFrame(experiments), use_container_width=True, hide_index=True)
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


def _browser_websocket_timeline(api_base_url: str, ws_base_url: str, job_id: str) -> None:
    ws_url = f"{ws_base_url.rstrip('/')}/ws/status/{job_id}"
    safe_url = json.dumps(ws_url)
    safe_api_url = json.dumps(api_base_url.rstrip('/'))
    safe_job_id = json.dumps(job_id)
    components.html(
        f"""
        <div id="timeline" style="height:420px; overflow:auto; border:1px solid rgba(156,176,205,.16); border-radius:8px; padding:12px; background:rgba(19,25,35,.74); font-family:Inter,Arial,sans-serif;"></div>
        <script>
        const timeline = document.getElementById("timeline");
        const seen = new Set();
        const socket = new WebSocket({safe_url});
        function addEvent(event) {{
            if (seen.has(event.id)) return;
            seen.add(event.id);
            const row = document.createElement("div");
            row.style.cssText = "border-left:3px solid #4cc9f0; padding:8px 10px; margin-bottom:8px; background:rgba(255,255,255,.04); border-radius:6px; color:#e8edf7;";
            if (event.status === "completed") row.style.borderLeftColor = "#7bd88f";
            if (event.status === "failed") row.style.borderLeftColor = "#ff6b6b";
            const agent = event.agent || "Runtime";
            row.innerHTML = `<b>${{agent}}</b> <span style="color:#91a0b8">(${{event.status}})</span><br><span>${{event.message}}</span>`;
            timeline.prepend(row);
        }}
        socket.onmessage = (message) => addEvent(JSON.parse(message.data));
        
        let pollingActive = false;
        function startHttpPolling() {{
            if (pollingActive) return;
            pollingActive = true;
            const errDiv = document.createElement("div");
            errDiv.style.cssText = "color:#f6c177; padding:8px 0; font-size: 0.85rem;";
            errDiv.textContent = "WebSocket stream offline. Polling updates via HTTP...";
            timeline.prepend(errDiv);
            
            async function poll() {{
                try {{
                    const response = await fetch(`${safe_api_url}/agent/jobs/${safe_job_id}`);
                    if (response.ok) {{
                        const data = await response.json();
                        const events = data.events || [];
                        events.forEach(addEvent);
                    }}
                }} catch (e) {{
                    console.error("HTTP fallback polling error:", e);
                }}
            }}
            poll();
            setInterval(poll, 2000);
        }}
        
        socket.onerror = () => startHttpPolling();
        socket.onclose = () => startHttpPolling();
        </script>
        """,
        height=450,
    )
