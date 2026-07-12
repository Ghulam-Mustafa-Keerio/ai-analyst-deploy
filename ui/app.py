from __future__ import annotations

from pathlib import Path
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui.state.app_state import init_state
from ui.theme import apply_theme
from ui.services import api_client


st.set_page_config(
    page_title="Agent OS — Autonomous Data Science",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_theme()
init_state()


def _connection_status() -> None:
    """Show a small live indicator for the configured backend."""
    url = st.session_state.api_base_url
    try:
        ok = api_client.run(api_client.health(url))
        connected = ok.get("status") == "ok"
    except Exception:
        connected = False
    if connected:
        st.markdown('<span class="badge success">● Backend online</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge danger">● Backend unreachable</span>', unsafe_allow_html=True)
    st.caption(url)


with st.sidebar:
    st.markdown("# 🧭 Agent OS")
    st.markdown(
        '<div class="eyebrow">Autonomous Data Science Control Plane</div>',
        unsafe_allow_html=True,
    )
    st.divider()

    page = st.radio(
        "Workspace",
        ["Dashboard", "Intelligence", "Advisor"],
        label_visibility="collapsed",
        captions=["Upload & launch", "Live reasoning", "Experiment Q&A"],
    )

    st.divider()
    with st.expander("Connection", expanded=False):
        st.session_state.api_base_url = st.text_input(
            "API base URL", st.session_state.api_base_url, key="api_url_input"
        )
        st.session_state.ws_base_url = st.text_input(
            "WebSocket base URL", st.session_state.ws_base_url, key="ws_url_input"
        )
        st.session_state.serverless = st.checkbox(
            "Serverless backend (single-request run)",
            st.session_state.serverless,
            help="Enable for Vercel/Function deployments where files and state do not persist between requests.",
        )
        _connection_status()

if page == "Dashboard":
    from ui.pages.dashboard import render_dashboard

    render_dashboard()
elif page == "Intelligence":
    from ui.pages.intelligence import render_intelligence

    render_intelligence()
else:
    from ui.pages.advisor import render_advisor

    render_advisor()
