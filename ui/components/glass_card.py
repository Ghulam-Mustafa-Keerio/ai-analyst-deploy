from __future__ import annotations

import streamlit as st


def glass_card(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="glass-card">
            <h3 style="margin-top:0">{title}</h3>
            <div class="small-muted">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
