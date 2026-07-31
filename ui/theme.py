from __future__ import annotations

import streamlit as st

# ---------------------------------------------------------------------------
# Design system
# ---------------------------------------------------------------------------
# Centralised, token-driven styling so every page shares one visual language.
# Clean, professional light-mode aesthetic suitable for a modern SaaS / data-
# science dashboard product.  Keep all raw CSS here; components and pages
# should only reference semantic class names.
# ---------------------------------------------------------------------------

PRIMARY = "#15803D"        # Discovery Green
SUCCESS = "#22C55E"        # Bright Green
WARNING = "#D97706"        # Amber
DANGER = "#DC2626"         # Red
TEXT = "#14532D"           # Deep Forest Green
MUTED = "#64748b"          # Slate 500
LINE = "rgba(148,163,184,0.22)"   # Slate 400 / 22%
PANEL = "rgba(240,253,244,0.82)"  # Soft Green Glass
PANEL_STRONG = "rgba(240,253,244,0.96)"
BASE = "#F0FDF4"           # Soft Mint background

CSS = """
/* ===== Import Google Fonts ===== */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --primary: #15803D;
    --primary-light: #22C55E;
    --primary-hover: #166534;
    --success: #22C55E;
    --success-light: #4ade80;
    --warning: #D97706;
    --warning-light: #f59e0b;
    --danger: #DC2626;
    --danger-light: #ef4444;
    --text: #14532D;
    --text-secondary: #166534;
    --muted: #64748b;
    --line: rgba(148,163,184,0.22);
    --panel: rgba(240,253,244,0.82);
    --panel-strong: rgba(240,253,244,0.96);
    --base: #F0FDF4;
    --base-alt: #dcfce7;
    --radius: 12px;
    --radius-lg: 16px;
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
    --shadow: 0 4px 16px rgba(0,0,0,0.06), 0 1px 4px rgba(0,0,0,0.04);
    --shadow-lg: 0 12px 40px rgba(0,0,0,0.08), 0 4px 12px rgba(0,0,0,0.04);
    --transition: 0.2s cubic-bezier(0.4,0,0.2,1);
}

/* ===== Global ===== */
.stApp {
    background:
        radial-gradient(1200px 600px at 80% -10%, rgba(21,128,61,0.05), transparent 60%),
        radial-gradient(900px 500px at -10% 10%, rgba(34,197,94,0.04), transparent 55%),
        var(--base) !important;
    color: var(--text);
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* Force all Streamlit text elements to dark color for readability */
.stApp, .stApp p, .stApp span, .stApp label, .stApp div {
    color: var(--text);
}
.stApp .stMarkdown, .stApp .stMarkdown p {
    color: var(--text);
}

/* ===== Typography ===== */
h1, h2, h3, h4 {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--text) !important;
}
h1 { font-size: 1.75rem; }
h2 { font-size: 1.35rem; }
h3 { font-size: 1.1rem; }
.small-muted {
    color: var(--muted);
    font-size: 0.85rem;
    line-height: 1.5;
}
.eyebrow {
    text-transform: uppercase;
    letter-spacing: 0.14em;
    font-size: 0.7rem;
    color: var(--muted);
    font-weight: 600;
}

/* ===== Cards ===== */
.card {
    background: var(--panel-strong);
    border: 1px solid var(--line);
    border-radius: var(--radius);
    padding: 20px;
    box-shadow: var(--shadow);
    backdrop-filter: blur(12px);
    transition: box-shadow var(--transition), transform var(--transition);
}
.card:hover {
    box-shadow: var(--shadow-lg);
    transform: translateY(-1px);
}
.card-strong {
    background: #ffffff;
    border: 1px solid var(--line);
    border-radius: var(--radius);
    padding: 20px;
    box-shadow: var(--shadow-sm);
}
.shell {
    background: linear-gradient(145deg, rgba(255,255,255,0.92), rgba(248,250,252,0.88));
    border: 1px solid var(--line);
    border-radius: var(--radius-lg);
    padding: 24px;
    box-shadow: var(--shadow);
}

/* ===== Metric tiles ===== */
.metric {
    background: #ffffff;
    border: 1px solid var(--line);
    border-radius: var(--radius);
    padding: 18px 20px;
    min-height: 96px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    box-shadow: var(--shadow-sm);
    transition: box-shadow var(--transition), transform var(--transition);
}
.metric:hover {
    box-shadow: var(--shadow);
    transform: translateY(-1px);
}
.metric .label {
    color: var(--muted);
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 600;
}
.metric .value {
    color: var(--text);
    font-size: 1.6rem;
    font-weight: 800;
    margin-top: 6px;
    line-height: 1.1;
}
.metric .hint {
    color: var(--muted);
    font-size: 0.78rem;
    margin-top: 4px;
}

/* ===== Agent pipeline nodes ===== */
.node {
    border: 1px solid var(--line);
    border-left: 4px solid var(--primary);
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 8px;
    background: #ffffff;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: var(--shadow-sm);
    transition: all var(--transition);
}
.node:hover {
    box-shadow: var(--shadow);
    transform: translateX(2px);
}
.node.completed { border-left-color: var(--success); }
.node.failed    { border-left-color: var(--danger); }
.node.queued    { border-left-color: var(--muted); opacity: 0.65; }
.node .name     { font-weight: 600; color: var(--text); }
.node .state {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding: 3px 10px;
    border-radius: 999px;
    border: 1px solid var(--line);
    color: var(--muted);
    font-weight: 500;
    background: var(--base);
}
.node.completed .state { color: var(--success); border-color: rgba(22,163,74,0.3); background: rgba(22,163,74,0.06); }
.node.failed .state    { color: var(--danger);  border-color: rgba(220,38,38,0.3);  background: rgba(220,38,38,0.06); }
.node.running .state   { color: var(--primary); border-color: rgba(21,128,61,0.3);  background: rgba(21,128,61,0.06); }

/* ===== Timeline rows ===== */
.tl-row {
    border-left: 3px solid var(--primary);
    padding: 10px 14px;
    margin-bottom: 8px;
    background: #ffffff;
    border-radius: 8px;
    color: var(--text);
    box-shadow: var(--shadow-sm);
    transition: all var(--transition);
}
.tl-row:hover {
    box-shadow: var(--shadow);
}
.tl-row.completed { border-left-color: var(--success); }
.tl-row.failed    { border-left-color: var(--danger); }
.tl-row .agent    { font-weight: 600; color: var(--text); }
.tl-row .msg      { color: var(--muted); font-size: 0.85rem; }

/* ===== Badges / pills ===== */
.badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.74rem;
    font-weight: 600;
    border: 1px solid var(--line);
    color: var(--muted);
    background: var(--base);
}
.badge.primary { color: var(--primary); border-color: rgba(21,128,61,0.3);  background: rgba(21,128,61,0.06); }
.badge.success { color: var(--success); border-color: rgba(22,163,74,0.3);  background: rgba(22,163,74,0.06); }
.badge.warning { color: var(--warning); border-color: rgba(217,119,6,0.3);  background: rgba(217,119,6,0.06); }
.badge.danger  { color: var(--danger);  border-color: rgba(220,38,38,0.3);  background: rgba(220,38,38,0.06); }

/* ===== Chat ===== */
.bubble {
    display: inline-block;
    max-width: 80%;
    border-radius: 14px;
    padding: 12px 16px;
    line-height: 1.5;
    border: 1px solid var(--line);
    box-shadow: var(--shadow-sm);
}
.bubble.user {
    background: linear-gradient(135deg, rgba(21,128,61,0.10), rgba(34,197,94,0.06));
    margin-left: auto;
    border-color: rgba(21,128,61,0.2);
}
.bubble.assistant {
    background: #ffffff;
}
.bubble .role {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--muted);
    margin-bottom: 4px;
    font-weight: 600;
}

/* ===== Empty state ===== */
.empty {
    text-align: center;
    padding: 52px 28px;
    border: 2px dashed var(--line);
    border-radius: var(--radius-lg);
    color: var(--muted);
    background: rgba(255,255,255,0.6);
}
.empty .icon { font-size: 2.2rem; margin-bottom: 12px; }

/* ===== Sidebar ===== */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f1f15 0%, #0a160e 100%) !important;
    border-right: 1px solid rgba(34,197,94,0.12);
}
section[data-testid="stSidebar"] * {
    color: #e2e8f0 !important;
}
section[data-testid="stSidebar"] .eyebrow {
    color: rgba(226,232,240,0.6) !important;
}
section[data-testid="stSidebar"] .badge {
    background: rgba(255,255,255,0.08);
    border-color: rgba(255,255,255,0.12);
}
section[data-testid="stSidebar"] .badge.success {
    color: #4ade80 !important;
    border-color: rgba(74,222,128,0.3);
    background: rgba(74,222,128,0.1);
}
section[data-testid="stSidebar"] .badge.danger {
    color: #f87171 !important;
    border-color: rgba(248,113,113,0.3);
    background: rgba(248,113,113,0.1);
}
section[data-testid="stSidebar"] .badge.primary {
    color: #4ade80 !important;
    border-color: rgba(74,222,128,0.3);
    background: rgba(74,222,128,0.1);
}
/* Sidebar radio labels */
section[data-testid="stSidebar"] label {
    color: #cbd5e1 !important;
}
section[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"] {
    color: #e2e8f0 !important;
}

.css-1oe6o3l, .st-emotion-cache-1oe6o3l { background: transparent !important; }

/* ===== Buttons ===== */
.stButton > button[kind="primary"],
.stButton > button[data-testid="stBaseButton-primary"] {
    background: linear-gradient(135deg, #15803D, #166534) !important;
    border: none;
    font-weight: 600;
    color: #ffffff !important;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(21,128,61,0.25);
    transition: all var(--transition);
}
.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="stBaseButton-primary"]:hover {
    box-shadow: 0 4px 16px rgba(21,128,61,0.35);
    transform: translateY(-1px);
}

/* ===== Streamlit input overrides ===== */
.stTextInput input, .stTextArea textarea, .stSelectbox select {
    background: #ffffff !important;
    border-color: var(--line) !important;
    color: var(--text) !important;
    border-radius: 8px !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(21,128,61,0.1) !important;
}

/* ===== Expander styling ===== */
.streamlit-expanderHeader {
    background: #ffffff !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    color: var(--text) !important;
}

/* ===== Dataframe ===== */
.stDataFrame {
    border-radius: var(--radius) !important;
    overflow: hidden;
    box-shadow: var(--shadow-sm);
}

/* ===== Progress bar background override ===== */
.stProgress > div > div {
    background: var(--base-alt) !important;
}

/* ===== Dividers ===== */
hr.soft {
    border: none;
    border-top: 1px solid var(--line);
    margin: 20px 0;
}

/* ===== Scrollbar ===== */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: rgba(148,163,184,0.3);
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(148,163,184,0.5);
}

/* ===== Tab / radio pills (horizontal) ===== */
.stRadio > div[role="radiogroup"] {
    gap: 6px;
}

/* ===== File uploader ===== */
.stFileUploader {
    border-radius: var(--radius) !important;
}

/* ===== Animations ===== */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes slideInLeft {
    from { opacity: 0; transform: translateX(-12px); }
    to   { opacity: 1; transform: translateX(0); }
}
@keyframes pulseGlow {
    0% { box-shadow: 0 0 0 0 rgba(21,128,61,0.4); }
    70% { box-shadow: 0 0 0 6px rgba(21,128,61,0); }
    100% { box-shadow: 0 0 0 0 rgba(21,128,61,0); }
}
@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}
@keyframes spin {
    to { transform: rotate(360deg); }
}
.card, .metric, .node, .tl-row, .bubble, .empty {
    animation: fadeIn 0.3s ease-out;
}
.node.running .state {
    animation: pulseGlow 2s infinite;
}

/* ===== User badge (sidebar) ===== */
.user-badge {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    border-radius: 10px;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.1);
    color: #e2e8f0;
    font-size: 0.88rem;
    font-weight: 600;
    margin-bottom: 8px;
    animation: slideInLeft 0.3s ease-out;
}
.user-badge span {
    color: #cbd5e1;
    font-weight: 500;
}

/* ===== Responsive layout ===== */
@media (max-width: 768px) {
    .stApp {
        font-size: 0.92rem;
    }
    h1 { font-size: 1.5rem; }
    h2 { font-size: 1.2rem; }
    h3 { font-size: 1rem; }
    .card, .card-strong, .shell {
        padding: 14px;
        border-radius: 10px;
    }
    .metric {
        padding: 12px 14px;
        min-height: 80px;
    }
    .metric .value {
        font-size: 1.3rem;
    }
    .node {
        padding: 10px 12px;
    }
    .bubble {
        max-width: 92%;
        padding: 10px 12px;
        font-size: 0.9rem;
    }
    .empty {
        padding: 32px 16px;
    }
    .empty .icon { font-size: 1.8rem; }
}

@media (max-width: 480px) {
    .stApp {
        font-size: 0.85rem;
    }
    h1 { font-size: 1.3rem; }
    .card, .card-strong, .shell {
        padding: 12px;
    }
    .metric .value {
        font-size: 1.15rem;
    }
    .auth-title {
        font-size: 1.5rem;
    }
}

/* ===== Loading spinner ===== */
.loading-spinner {
    display: inline-block;
    width: 18px;
    height: 18px;
    border: 2px solid rgba(21,128,61,0.2);
    border-top-color: var(--primary);
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
}

/* ===== Smooth page transitions ===== */
.stMainBlock {
    animation: fadeInUp 0.35s ease-out;
}

/* ===== Better mobile sidebar toggle ===== */
@media (max-width: 768px) {
    section[data-testid="stSidebar"] {
        min-width: 260px;
    }
}
"""


def apply_theme() -> None:
    """Inject the design-system CSS once per session."""
    if "theme_applied" not in st.session_state:
        st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)
        st.session_state.theme_applied = True


def render_css() -> None:
    """Render the raw CSS block (used at app bootstrap)."""
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

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
