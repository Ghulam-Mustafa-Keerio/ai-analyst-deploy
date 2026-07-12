from __future__ import annotations

import streamlit as st


def glass_card(title: str, body: str) -> None:
    """Render a titled panel using the shared design system."""
    st.markdown(
        f"""
        <div class="card">
            <h3 style="margin-top:0">{title}</h3>
            <div class="small-muted">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
