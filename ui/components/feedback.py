from __future__ import annotations

import streamlit as st


def status_badge(text: str, kind: str = "") -> None:
    """Render a pill badge. kind: '', 'primary', 'success', 'warning', 'danger'."""
    cls = f"badge {kind}" if kind else "badge"
    st.markdown(f'<span class="{cls}">{text}</span>', unsafe_allow_html=True)


def agent_node(name: str, state: str) -> None:
    """Render a single agent pipeline node with a status pill."""
    state_cls = {
        "completed": "completed",
        "failed": "failed",
        "running": "running",
    }.get(state, "queued")
    st.markdown(
        f"""
        <div class="node {state_cls}">
            <span class="name">{name}</span>
            <span class="state">{state}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def progress_bar(completed: int, total: int) -> None:
    """Render a labelled progress bar for pipeline completion."""
    pct = int(round(100 * completed / total)) if total else 0
    st.markdown(
        f"""
        <div style="margin:6px 0 14px;">
            <div style="display:flex; justify-content:space-between; font-size:0.8rem; color:var(--muted); margin-bottom:6px;">
                <span>Pipeline progress</span><span>{completed}/{total} stages</span>
            </div>
            <div style="height:8px; border-radius:999px; background:rgba(255,255,255,0.06); overflow:hidden; border:1px solid var(--line);">
                <div style="height:100%; width:{pct}%; background:linear-gradient(90deg,#4cc9f0,#7bd88f); transition:width .4s ease;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def empty_state(icon: str, title: str, body: str) -> None:
    """Render a friendly empty state for pages that need input first."""
    st.markdown(
        f"""
        <div class="empty">
            <div class="icon">{icon}</div>
            <div style="font-size:1.05rem; color:var(--text); font-weight:600; margin-bottom:6px;">{title}</div>
            <div class="small-muted">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def timeline_row(agent: str, message: str, status: str) -> None:
    """Render a single reasoning-timeline row."""
    cls = {"completed": "completed", "failed": "failed"}.get(status, "")
    st.markdown(
        f"""
        <div class="tl-row {cls}">
            <span class="agent">{agent}</span>
            <span class="small-muted"> &middot; {status}</span>
            <div class="msg">{message}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
