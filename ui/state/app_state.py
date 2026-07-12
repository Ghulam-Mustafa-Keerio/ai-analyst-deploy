from __future__ import annotations

import os

import streamlit as st


def init_state() -> None:
    defaults = {
        "api_base_url": os.environ.get("API_BASE_URL", "http://127.0.0.1:8000"),
        "ws_base_url": os.environ.get("WS_BASE_URL", "ws://127.0.0.1:8000"),
        "serverless": os.environ.get("SERVERLESS_BACKEND", "false").lower() in {"1", "true", "yes"},
        "dataset": None,
        "profile": None,
        "job_id": None,
        "events": [],
        "last_experiments": [],
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def append_events(events: list[dict]) -> None:
    seen = {event.get("id") for event in st.session_state.events}
    st.session_state.events.extend(event for event in events if event.get("id") not in seen)
