import streamlit as st
from typing import Any, List, Dict, Callable, cast

cache_data = cast(Callable[..., Callable[..., object]], st.cache_data)

# --- Intelligence Dashboard Styles ---
INSIGHT_CARD = "bg-white/5 p-4 rounded-lg shadow-lg border border-gray-800 rounded-xl transition-all duration-200 transform"

# --- Data Explorer Component ---
@cache_data
def render_data_explorer(data: List[Dict[str, Any]]) -> None:
    st.markdown("""<style> .data-explorer {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 1.5rem;
        padding: 2rem;
    } .data-card {
        background: var(--bg-card);
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    } </style>""", unsafe_allow_html=True)

    explorer = "<div class='data-explorer'>"
    for item in data:
        explorer += f"<div class='data-card'>"
        for key, value in item.items():
            explorer += f"<div class='data-item'>\n  <span class='data-key'>{key}</span>\n  <span class='data-value'>{value}</span>\n</div>"
        explorer += "</div>"
    explorer += "</div>"
    st.markdown(explorer, unsafe_allow_html=True)

# --- Insight Cards ---
@cache_data
def render_insight_cards(insights: List[Dict[str, str]]) -> None:
    cards = "<div class='insight-cards'>"
    for insight in insights:
        cards += f"<div class='insight-card'>\n  <h3>{insight['title']}</h3>\n  <p>{insight['description']}</p>\n</div>"
    cards += "</div>"
    st.markdown(cards, unsafe_allow_html=True)

# --- Main Intelligence View ---
@cache_data
def render_intelligence_view() -> None:
    st.markdown("""<style> .intelligence-view {
        max-width: 120rem;
        padding: 4rem 6rem;
        margin: 0 auto;
    } </style>""", unsafe_allow_html=True)

    with st.container():
        st.markdown("<h1 class='dashboard-title'>🧠 Intelligence Dashboard</h1>", unsafe_allow_html=True)
        render_data_explorer([{
            'field': 'User Engagement',
            'value': 'High'
        }, {
            'field': 'Data Quality',
            'value': '93%'
        }])
        render_insight_cards([{
            'title': 'Key Insight 1',
            'description': 'User retention increased by 25%'
        }, {
            'title': 'Key Insight 2',
            'description': 'Data completeness at 98%'
        }])

# --- Type Annotations for Pylance ---
@cache_data
def get_sample_data() -> List[str]:
    return ["Sample Data 1", "Sample Data 2"]

@cache_data
def process_data(data: List[str]) -> List[Dict[str, str]]:
    return [{"processed": item} for item in data]