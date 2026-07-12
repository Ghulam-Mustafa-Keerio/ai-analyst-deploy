from __future__ import annotations

import streamlit as st


def chat_bubble(role: str, content: str) -> None:
    align = "right" if role == "user" else "left"
    color = "rgba(76,201,240,.14)" if role == "user" else "rgba(255,255,255,.06)"
    st.markdown(
        f"""
        <div style="text-align:{align}; margin: 8px 0;">
            <span style="display:inline-block; max-width: 78%; background:{color}; border:1px solid var(--line); border-radius:8px; padding:10px 12px;">
                {content}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )
