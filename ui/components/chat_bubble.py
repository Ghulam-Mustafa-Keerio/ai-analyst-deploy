from __future__ import annotations

import streamlit as st


def chat_bubble(role: str, content: str) -> None:
    """Render a chat message bubble using the shared design system."""
    cls = "user" if role == "user" else "assistant"
    label = "You" if role == "user" else "Advisor"
    st.markdown(
        f"""
        <div style="display:flex; justify-content:{'flex-end' if role == 'user' else 'flex-start'}; margin:10px 0;">
            <div class="bubble {cls}">
                <div class="role">{label}</div>
                <div>{content}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
