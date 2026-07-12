from __future__ import annotations

import streamlit as st

from ui.components.chat_bubble import chat_bubble
from ui.services import api_client


def render_advisor() -> None:
    st.title("Advisor")
    st.caption("Experiment-aware guidance grounded in the active agent run.")

    st.session_state.setdefault("advisor_messages", [])
    for message in st.session_state.advisor_messages:
        chat_bubble(message["role"], message["content"])

    prompt = st.chat_input("Ask about model choice, metrics, features, or next experiments")
    if not prompt:
        return

    st.session_state.advisor_messages.append({"role": "user", "content": prompt})
    chat_bubble("user", prompt)
    response = api_client.run(
        api_client.chat(st.session_state.api_base_url, job_id=st.session_state.job_id, message=prompt)
    )
    answer = response["answer"]
    st.session_state.advisor_messages.append({"role": "assistant", "content": answer})
    chat_bubble("assistant", answer)
