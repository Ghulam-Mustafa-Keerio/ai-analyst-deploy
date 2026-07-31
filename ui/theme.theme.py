# ...existing code...
@media (max-width: 768px) {
    section[data-testid="stSidebar"] {
        min-width: 260px;
    }
}

/* ===== Cyberpunk Visual Effects ===== */
/* Neon glow for cards and interactive elements */
.card, .node, .metric, .shell {
    box-shadow: 0 0 0 1px rgba(21,128,61,0.15), 0 4px 16px rgba(21,128,61,0.08), 0 1px 4px rgba(0,0,0,0.06);
}
.card:hover, .node:hover, .metric:hover {
    box-shadow: 0 0 0 1px rgba(34,197,94,0.35), 0 8px 32px rgba(21,128,61,0.25), 0 0 20px rgba(34,197,94,0.15);
}
/* Terminal-style borders for sidebar and panels */
section[data-testid="stSidebar"] {
    border-right: 2px solid rgba(34,197,94,0.15) !important;
    box-shadow: inset -4px 0 12px rgba(21,128,61,0.1) !important;
}
/* Scanline overlay effect */
.stApp::before {
    content: "";
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    pointer-events: none;
    background: repeating-linear-gradient(
        0deg,
        rgba(21,128,61,0.015) 0px,
        rgba(21,128,61,0.015) 1px,
        transparent 1px,
        transparent 2px
    );
    z-index: 9999;
    opacity: 0.4;
}
/* Neon glow pulse for active/running states */
.node.running, .badge.primary {
    animation: pulseGlow 2.5s infinite ease-in-out;
    border-color: rgba(34,197,94,0.5) !important;
}
/* Terminal-style input borders */
.stTextInput input, .stTextArea textarea, .stSelectbox select {
    border: 1px solid rgba(21,128,61,0.25) !important;
    box-shadow: inset 0 1px 3px rgba(21,128,61,0.05) !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: rgba(34,197,94,0.6) !important;
    box-shadow: 0 0 0 3px rgba(21,128,61,0.15), 0 0 12px rgba(34,197,94,0.2) !important;
}

"""
def apply_theme() -> None:
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)
def render_css() -> None:
    """Render the raw CSS block (used at app bootstrap)."""
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)
"""