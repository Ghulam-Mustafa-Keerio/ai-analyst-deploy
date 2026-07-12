from __future__ import annotations

import streamlit as st


def metric_card(label: str, value: str | int | float, hint: str = "", accent: str = "") -> None:
    """Render a single metric tile using the shared design system."""
    style = f"border-top: 2px solid {accent};" if accent else ""
    st.markdown(
        f"""
        <div class="metric" style="{style}">
            <div class="label">{label}</div>
            <div class="value">{value}</div>
            <div class="hint">{hint}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
