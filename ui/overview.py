import streamlit as st
from typing import List, Dict, Optional

# --- Global CSS Classes ---
GLASS_CARD = "bg-white/5 p-6 rounded-lg shadow-lg border border-gray-800 rounded-xl transition-all duration-200 transform"

# --- Sidebar Custom Header ---
@st.cache_data
def render_sidebar_header() -> None:
    st.markdown("""<style> .sidebar-header {
    padding: 1rem;
    border-bottom: 1px solid var(--border-color);
}
</style>""", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([3, 1, 2])
    with col1:
        st.markdown("""<div class='sidebar-header'>🧭 Agent OS — Autonomous Control Plane</div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""<div class='status-pill'>Backend Online <span class='status-dot'></span></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""<div class='user-profile'>👤 User: {st.session_state.user}</div>""", unsafe_allow_html=True)

# --- Hero Banner ---
@st.cache_data
def render_hero_banner(title: str, subtitle: str, step_number: Optional[int] = None) -> None:
    banner = f"<div class='hero-banner'>"
    if step_number is not None:
        banner += f"<div class='step-badge'>{step_number}</div>"
    banner += f"<h1>{title}</h1><p>{subtitle}</p>"
    banner += "</div>"
    st.markdown(banner, unsafe_allow_html=True)

# --- Quick Start Grid ---
@st.cache_data
def render_quick_start_grid(items: List[Dict[str, str]]) -> None:
    grid = "<div class='quick-start-grid'>"
    for item in items:
        grid += f"<div class='grid-item'>"
        grid += f"<h3>{item['title']}</h3>"
        grid += f"<p>{item['description']}</p>"
        grid += "</div>"
    grid += "</div>"
    st.markdown(grid, unsafe_allow_html=True)

# --- Autonomy Modes Section ---
@st.cache_data
def render_autonomy_modes() -> None:
    st.markdown("""<style> .mode-card {
    background: var(--bg-card);
    border-radius: 10px;
    padding: 1.25rem;
    margin: 1rem;
} .mode-card h2 {
    color: var(--text-primary);
} </style>""", unsafe_allow_html=True)

    with st.container():
        st.markdown("<h2 class='section-title'>Autonomy Modes</h2>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div class='mode-card'> <h2>🔧 Manual Mode</h2> <p>Direct model selection and manual hyperparameter tuning</p> </div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='mode-card'> <h2>🤝 Assisted Mode</h2> <p>Deterministic selection with guided recommendations</p> </div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='mode-card'> <h2>🧠 Autonomous Mode</h2> <p>Multi-agent debate engine with automated feature engineering</p> </div>", unsafe_allow_html=True)

# --- Main Execution ---
if __name__ == '__main__':
    render_sidebar_header()
    render_hero_banner('AI Analyst Platform', 'Intelligent Decision Making Made Easy', 1)
    quick_start_items = [
        {'title': '1. Connect Data', 'description': 'Import and connect your data sources'},
        {'title': '2. Train Models', 'description': 'Build and train AI models'},
        {'title': '3. Deploy', 'description': 'Deploy models to production environment'}
    ]
    render_quick_start_grid(quick_start_items)
    render_styled_section_header('Getting Started', 1)