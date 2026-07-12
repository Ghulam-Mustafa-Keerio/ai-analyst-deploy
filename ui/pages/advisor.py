from __future__ import annotations

import streamlit as st

from ui.components.chat_bubble import chat_bubble
from ui.components.feedback import empty_state
from ui.services import api_client


def render_advisor() -> None:
    st.markdown('<div class="eyebrow">Workspace / Advisor</div>', unsafe_allow_html=True)
    st.title("Advisor")
    st.caption("Experiment-aware guidance grounded in the active agent run.")

    st.session_state.setdefault("advisor_messages", [])

    if not st.session_state.job_id:
        empty_state(
            "💬",
            "No active run to advise on",
            "Start an agent run from the Dashboard, then return here to ask about model choice, metrics, features, or next experiments.",
        )
        return

    for message in st.session_state.advisor_messages:
        chat_bubble(message["role"], message["content"])

    prompt = st.chat_input("Ask about model choice, metrics, features, or next experiments")
    if not prompt:
        return

    st.session_state.advisor_messages.append({"role": "user", "content": prompt})
    chat_bubble("user", prompt)

    with st.spinner("Advisor is thinking…"):
        try:
            response = api_client.run(
                api_client.chat(st.session_state.api_base_url, job_id=st.session_state.job_id, message=prompt)
            )
            answer = response["answer"]
        except Exception as exc:
            answer = f"Unable to reach the advisor: {exc}"

    st.session_state.advisor_messages.append({"role": "assistant", "content": answer})
    chat_bubble("assistant", answer)
