from __future__ import annotations

from pathlib import Path
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui.pages.advisor import render_advisor
from ui.pages.dashboard import render_dashboard
from ui.pages.intelligence import render_intelligence
from ui.state.app_state import init_state


st.set_page_config(page_title="Agent OS v2", page_icon=None, layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
    <style>
    :root {
        --base: #0b0e14;
        --panel: rgba(19, 25, 35, 0.74);
        --panel-strong: rgba(27, 36, 50, 0.92);
        --line: rgba(156, 176, 205, 0.16);
        --text: #e8edf7;
        --muted: #91a0b8;
        --blue: #4cc9f0;
        --green: #7bd88f;
        --amber: #f6c177;
        --red: #ff6b6b;
    }
    .stApp { background: var(--base); color: var(--text); }
    h1, h2, h3 { letter-spacing: 0; }
    .agent-shell {
        border: 1px solid var(--line);
        background: linear-gradient(145deg, rgba(18,24,34,.86), rgba(13,17,24,.82));
        border-radius: 8px;
        padding: 18px;
        box-shadow: 0 18px 60px rgba(0,0,0,.24);
    }
    .glass-card {
        border: 1px solid var(--line);
        background: var(--panel);
        backdrop-filter: blur(14px);
        border-radius: 8px;
        padding: 16px;
    }
    .metric-card {
        border: 1px solid var(--line);
        background: var(--panel-strong);
        border-radius: 8px;
        padding: 14px;
        min-height: 96px;
    }
    .metric-label { color: var(--muted); font-size: .82rem; text-transform: uppercase; }
    .metric-value { color: var(--text); font-size: 1.55rem; font-weight: 700; margin-top: 8px; }
    .agent-node {
        border: 1px solid var(--line);
        border-left: 4px solid var(--blue);
        border-radius: 8px;
        padding: 10px 12px;
        margin-bottom: 8px;
        background: rgba(255,255,255,.03);
    }
    .agent-node.completed { border-left-color: var(--green); }
    .agent-node.failed { border-left-color: var(--red); }
    .small-muted { color: var(--muted); font-size: .85rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

init_state()

with st.sidebar:
    st.markdown("## Agent OS v2")
    st.caption("Autonomous data science control plane")
    page = st.radio("Workspace", ["Dashboard", "Intelligence", "Advisor"], label_visibility="collapsed")
    st.divider()
    st.session_state.api_base_url = st.text_input("API base URL", st.session_state.api_base_url)
    st.session_state.ws_base_url = st.text_input("WebSocket base URL", st.session_state.ws_base_url)
    st.session_state.serverless = st.checkbox("Serverless backend (single-request run)", st.session_state.serverless)

if page == "Dashboard":
    render_dashboard()
elif page == "Intelligence":
    render_intelligence()
else:
    render_advisor()
