from __future__ import annotations

import streamlit as st


def metric_card(label: str, value: str | int | float, hint: str = "") -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="small-muted">{hint}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
