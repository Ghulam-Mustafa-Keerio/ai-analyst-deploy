from __future__ import annotations

from pathlib import Path
import sys

import streamlit as st

# Inject global CSS
CSS = """/* 1. Global Reset & Theme Variables */
:root {
  --bg-main: #090d16;
  --bg-card: rgba(30, 41, 59, 0.6);
  --border-color: rgba(148, 163, 184, 0.15);
  --primary-blue: #2563eb;
  --accent-blue: #60a5fa;
  --text-primary: #f8fafc;
  --text-secondary: #94a3b8;
}

/* 2. Hide Native Streamlit Elements */
[data-testid="stSidebarNav"] {
  display: none !important;
}
header[data-testid="stHeader"] {
  background: transparent !important;
}

/* 3. Global Canvas & Background */
[ data-testid="stAppViewContainer"] {
  background: linear-gradient(135deg, var(--bg-main) 0%, #0f172a 100%) !important;
  color: var(--text-primary) !important;
}

/* 4. Sidebar Refinement */
[data-testid="stSidebar"] {
  background-color: rgba(15, 23, 42, 0.95) !important;
  border-right: 1px solid var(--border-color) !important;
}

/* 5. Main Content Area Spacing */
[ data-testid="stMainBlockContainer"] {
  max-width: 1150px !important;
  padding-top: 2rem !important;
  padding-bottom: 3rem !important;
}

/* Additional UI Polish CSS */

/* 1. Enhanced Sidebar Navigation Styles */
[ data-testid="stSidebar"] div[role="radiogroup"] {
  background: transparent !important;
  border: none !important;
  display: flex !important;
  flex-direction: column !important;
  gap: 6px !important;
}

[ data-testid="stSidebar"] div[role="radiogroup"] label {
  padding: 10px 14px !important;
  border-radius: 10px !important;
  background: rgba(30, 41, 59, 0.4) !important;
  border: 1px solid rgba(148, 163, 184, 0.1) !important;
  color: #94a3b8 !important;
  font-weight: 600 !important;
  transition: all 0.2s ease !important;
  cursor: pointer !important;
}

[ data-testid="stSidebar"] div[role="radiogroup"] label:hover {
  background: rgba(30, 41, 59, 0.8) !important;
  color: #ffffff !important;
}

[ data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
  color: #ffffff !important;
  border-color: #3b82f6 !important;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
}

/* 2. Segmented Control for Autonomy Switch */
.main div[role="radiogroup"] {
  background: rgba(15, 23, 42, 0.8) !important;
  padding: 6px !important;
  border-radius: 12px !important;
  border: 1px solid rgba(148, 163, 184, 0.2) !important;
  display: flex !important;
  gap: 6px !important;
}

.main div[role="radiogroup"] label {
  flex: 1 !important;
  text-align: center !important;
  padding: 8px 16px !important;
  border-radius: 8px !important;
  color: #94a3b8 !important;
  font-weight: 600 !important;
  background: transparent !important;
  transition: all 0.2s ease !important;
}

.main div[role="radiogroup"] label:has(input:checked) {
  background: #2563eb !important;
  color: #ffffff !important;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
}

/* 3. Filter Chips Container */
.filter-container {
  background: rgba(30, 41, 59, 0.5);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 16px;
  padding: 1.25rem 1.5rem;
  margin-bottom: 1.5rem;
}

.filter-pills-wrapper {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 0.75rem;
}

.filter-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 9999px;
  background: rgba(15, 23, 42, 0.7);
  border: 1px solid rgba(148, 163, 184, 0.25);
  color: #f8fafc;
  font-size: 0.85rem;
  font-weight: 600;
  transition: all 0.2s ease-in-out;
}

.filter-chip:hover {
  border-color: #60a5fa;
  background: rgba(37, 99, 235, 0.2);
}

/* 4. Enhanced Section Headers */
.styled-section-header {
  padding: 1rem 1.5rem;
  background: rgba(15, 23, 42, 0.3);
  border-radius: 10px;
  margin-bottom: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.step-badge {
  background: rgba(37, 99, 235, 0.2);
  padding: 4px 12px;
  border-radius: 12px;
  color: #ffffff;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
}

"""

st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

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

if not st.session_state.get("authenticated", False):
    from ui.pages.auth import render_auth
    render_auth()
    st.stop()


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

    # User badge + logout
    username = st.session_state.get("username", "User")
    st.markdown(
        f'<div class="user-badge">👤 <span>{username}</span></div>',
        unsafe_allow_html=True,
    )
    if st.button("Sign out", use_container_width=True, key="logout_btn"):
        for key in ("authenticated", "username"):
            st.session_state.pop(key, None)
        st.rerun()
    st.divider()

    page = st.radio(
        "Workspace",
        ["Overview", "Dashboard", "Intelligence", "Advisor", "Integrations"],
        label_visibility="collapsed",
        captions=["Platform guidelines", "Upload & launch", "Live reasoning", "Experiment Q&A", "MCP & MLOps"],
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

if page == "Overview":
    from ui.pages.overview import render_overview
    render_overview()
elif page == "Dashboard":
    from ui.pages.dashboard import render_dashboard
    render_dashboard()
elif page == "Intelligence":
    from ui.pages.intelligence import intelligence_page as render_intelligence
    render_intelligence()
elif page == "Integrations":
    from ui.pages.integrations import render_integrations
    render_integrations()
else:
    from ui.pages.advisor import render_advisor
    render_advisor()
