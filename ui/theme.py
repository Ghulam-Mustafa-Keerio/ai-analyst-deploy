from __future__ import annotations

import streamlit as st

# ---------------------------------------------------------------------------
# Design system
# ---------------------------------------------------------------------------
# Centralised, token-driven styling so every page shares one visual language.
# Colours follow a dark, high-contrast "control plane" aesthetic suitable for
# an autonomous data-science product. Keep all raw CSS here; components and
# pages should only reference semantic class names.
# ---------------------------------------------------------------------------

PRIMARY = "#4cc9f0"
SUCCESS = "#7bd88f"
WARNING = "#f6c177"
DANGER = "#ff6b6b"
TEXT = "#e8edf7"
MUTED = "#91a0b8"
LINE = "rgba(156,176,205,0.16)"
PANEL = "rgba(19,25,35,0.74)"
PANEL_STRONG = "rgba(27,36,50,0.92)"
BASE = "#0b0e14"

CSS = """
:root {
    --primary: #4cc9f0;
    --success: #7bd88f;
    --warning: #f6c177;
    --danger: #ff6b6b;
    --text: #e8edf7;
    --muted: #91a0b8;
    --line: rgba(156,176,205,0.16);
    --panel: rgba(19,25,35,0.74);
    --panel-strong: rgba(27,36,50,0.92);
    --base: #0b0e14;
    --radius: 12px;
    --shadow: 0 18px 60px rgba(0,0,0,0.28);
}

.stApp {
    background:
        radial-gradient(1200px 600px at 80% -10%, rgba(76,201,240,0.08), transparent 60%),
        radial-gradient(900px 500px at -10% 10%, rgba(123,216,143,0.06), transparent 55%),
        var(--base);
    color: var(--text);
}

/* Typography */
h1, h2, h3, h4 { font-weight: 650; letter-spacing: -0.01em; }
h1 { font-size: 1.7rem; }
h2 { font-size: 1.3rem; }
h3 { font-size: 1.05rem; }
.small-muted { color: var(--muted); font-size: 0.85rem; line-height: 1.45; }
.eyebrow {
    text-transform: uppercase;
    letter-spacing: 0.14em;
    font-size: 0.7rem;
    color: var(--muted);
    font-weight: 600;
}

/* Cards */
.card {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: var(--radius);
    padding: 18px;
    box-shadow: var(--shadow);
    backdrop-filter: blur(14px);
}
.card-strong {
    background: var(--panel-strong);
    border: 1px solid var(--line);
    border-radius: var(--radius);
    padding: 18px;
}
.shell {
    background: linear-gradient(145deg, rgba(18,24,34,0.86), rgba(13,17,24,0.82));
    border: 1px solid var(--line);
    border-radius: 16px;
    padding: 22px;
    box-shadow: var(--shadow);
}

/* Metric tiles */
.metric {
    background: var(--panel-strong);
    border: 1px solid var(--line);
    border-radius: var(--radius);
    padding: 16px 18px;
    min-height: 92px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}
.metric .label {
    color: var(--muted);
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
.metric .value {
    color: var(--text);
    font-size: 1.6rem;
    font-weight: 700;
    margin-top: 6px;
    line-height: 1.1;
}
.metric .hint { color: var(--muted); font-size: 0.78rem; margin-top: 4px; }

/* Agent pipeline nodes */
.node {
    border: 1px solid var(--line);
    border-left: 4px solid var(--primary);
    border-radius: 10px;
    padding: 10px 14px;
    margin-bottom: 8px;
    background: rgba(255,255,255,0.03);
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.node.completed { border-left-color: var(--success); }
.node.failed { border-left-color: var(--danger); }
.node.queued { border-left-color: var(--muted); opacity: 0.7; }
.node .name { font-weight: 600; }
.node .state {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding: 2px 8px;
    border-radius: 999px;
    border: 1px solid var(--line);
    color: var(--muted);
}
.node.completed .state { color: var(--success); border-color: rgba(123,216,143,0.4); }
.node.failed .state { color: var(--danger); border-color: rgba(255,107,107,0.4); }
.node.running .state { color: var(--primary); border-color: rgba(76,201,240,0.4); }

/* Timeline rows */
.tl-row {
    border-left: 3px solid var(--primary);
    padding: 9px 12px;
    margin-bottom: 8px;
    background: rgba(255,255,255,0.04);
    border-radius: 8px;
    color: var(--text);
}
.tl-row.completed { border-left-color: var(--success); }
.tl-row.failed { border-left-color: var(--danger); }
.tl-row .agent { font-weight: 600; }
.tl-row .msg { color: var(--muted); font-size: 0.85rem; }

/* Badges / pills */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 0.74rem;
    font-weight: 600;
    border: 1px solid var(--line);
    color: var(--muted);
}
.badge.primary { color: var(--primary); border-color: rgba(76,201,240,0.4); }
.badge.success { color: var(--success); border-color: rgba(123,216,143,0.4); }
.badge.warning { color: var(--warning); border-color: rgba(246,193,119,0.4); }
.badge.danger { color: var(--danger); border-color: rgba(255,107,107,0.4); }

/* Chat */
.bubble {
    display: inline-block;
    max-width: 80%;
    border-radius: 14px;
    padding: 10px 14px;
    line-height: 1.5;
    border: 1px solid var(--line);
}
.bubble.user { background: rgba(76,201,240,0.14); margin-left: auto; }
.bubble.assistant { background: rgba(255,255,255,0.06); }
.bubble .role { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); margin-bottom: 4px; }

/* Empty state */
.empty {
    text-align: center;
    padding: 48px 24px;
    border: 1px dashed var(--line);
    border-radius: var(--radius);
    color: var(--muted);
    background: rgba(255,255,255,0.02);
}
.empty .icon { font-size: 2rem; margin-bottom: 10px; }

/* Sidebar polish */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(13,17,24,0.96), rgba(11,14,20,0.96));
    border-right: 1px solid var(--line);
}
.css-1oe6o3l, .st-emotion-cache-1oe6o3l { background: transparent !important; }

/* Buttons */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #4cc9f0, #3aa0d6);
    border: none;
    font-weight: 600;
}

/* Dividers */
hr.soft { border: none; border-top: 1px solid var(--line); margin: 18px 0; }
"""


def apply_theme() -> None:
    """Inject the design-system CSS once per session."""
    if "theme_applied" not in st.session_state:
        st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)
        st.session_state.theme_applied = True


def render_css() -> None:
    """Render the raw CSS block (used at app bootstrap)."""
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)
