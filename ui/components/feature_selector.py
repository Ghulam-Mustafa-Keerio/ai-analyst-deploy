from __future__ import annotations

import streamlit as st


def feature_selector(columns: list[str], target: str | None) -> list[str]:
    options = [column for column in columns if column != target]
    return st.multiselect("Features", options, default=options[: min(8, len(options))])
