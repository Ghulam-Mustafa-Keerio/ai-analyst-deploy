import streamlit as st
from typing import List, Dict

# --- Global CSS Classes ---
GLASS_CARD = "bg-white/5 p-6 rounded-lg shadow-lg border border-gray-800 rounded-xl transition-all duration-200 transform"

# --- Custom Sidebar Header ---
@st.cache_data
def render_custom_sidebar(header_text: str, status: str, user: str = "Guest") -> None:
    st.markdown("""<style> .custom-sidebar {\n    background: var(--bg-sidebar);\n    padding: 1rem;\n    border-right: 1px solid var(--border-color);\n}\n.custom-sidebar-header {\n    font-weight: 600;\n    margin-bottom: 1rem;\n}\n.custom-sidebar-item {\n    margin: 0.5rem 0;\n}\n</style>""", unsafe_allow_html=True)

    st.markdown(f"<div class='custom-sidebar'>\n  <div class='custom-sidebar-header'>{header_text}</div>\n  <div class='custom-sidebar-item'>Status: {status}</div>\n  <div class='custom-sidebar-item'>User: {user}</div>\n</div>", unsafe_allow_html=True)

# --- Filter Chips ---
@st.cache_data
def render_filter_chips(filters: List[Dict[str, str]]) -> None:
    chips = "<div class='filter-chips'>"
    for filter in filters:
        chips += f"<div class='filter-chip'>{filter['label']}</div>"
    chips += "</div>"
    st.markdown(chips, unsafe_allow_html=True)

# --- Segmented Control ---
@st.cache_data
def render_segmented_control(options: List[str], selected: str) -> None:
    control = "<div class='segmented-control'>"
    for option in options:
        selected_class = " selected" if option == selected else ""
        control += f"<div class='option{selected_class}'>{option}</div>"
    control += "</div>"
    st.markdown(control, unsafe_allow_html=True)

# --- Dashboard Card ---
@st.cache_data
def render_dashboard_card(title: str, content: str) -> None:
    st.markdown("""<div class='dashboard-card'>\n  <h3>{title}</h3>\n  <p>{content}</p>\n</div>""", unsafe_allow_html=True)

if __name__ == '__main__':
    # Example implementation
    render_custom_sidebar("Launch Agent Pipeline", "Running", "User123")
    filters = [
        {"label": "Region"},
        {"label": "Channel"},
        {"label": "Product category"},
        {"label": "Customer segment"},
    ]
    render_filter_chips(filters)
    render_segmented_control(['Manual', 'Assisted', 'Autonomous'], 'Autonomous')
    render_dashboard_card('Launch Agent Pipeline', 'This is the launch agent pipeline.')