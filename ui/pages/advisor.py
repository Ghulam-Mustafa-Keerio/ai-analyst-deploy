from __future__ import annotations

import logging
import streamlit as st
import httpx

from ui.components.chat_bubble import chat_bubble
from ui.components.feedback import empty_state
from ui.components.plot_3d import scatter_3d
from ui.services import api_client

logger = logging.getLogger(__name__)


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

    dataset = st.session_state.dataset
    if dataset:
        with st.expander("3D dataset context", expanded=False):
            st.caption("PCA projection of the active dataset, grounding the advisor's reasoning.")
            try:
                embedding = api_client.run(api_client.embed_3d(st.session_state.api_base_url, dataset["dataset_id"]))
                scatter_3d(embedding.get("points", []), color="#16a34a")
            except httpx.HTTPStatusError as exc:
                st.info(f"3D context unavailable: {exc}")

    for message in st.session_state.advisor_messages:
        chat_bubble(message["role"], message["content"])

    prompt = st.chat_input("Ask about model choice, metrics, features, or next experiments")
    if not prompt:
        return

    st.session_state.advisor_messages.append({"role": "user", "content": prompt})
    chat_bubble("user", prompt)

    with st.spinner("Advisor is thinking…"):
        try:
            response = api_client.run(api_client.chat(st.session_state.api_base_url, job_id=st.session_state.job_id, message=prompt))
            # [+] Reliability: Use .get() for safe access. If the "answer" key is missing,
            # this prevents a KeyError and provides a graceful fallback message.
            answer = response.get("answer", "I'm sorry, I encountered an issue and couldn't form a response.")
        except httpx.ConnectError:
            answer = "Unable to reach the advisor: Connection failed. Please check the backend server."
        except httpx.HTTPStatusError as exc:
            answer = f"Unable to reach the advisor: Server returned status {exc.response.status_code}."
        except Exception as exc:
            logger.error(f"Advisor chat failed unexpectedly: {exc}", exc_info=True)
            # [+] UX/Security: Show a generic error to the user instead of leaking implementation details.
            # The full error is logged for debugging.
            answer = "An unexpected error occurred. Please check the logs for more details."

    st.session_state.advisor_messages.append({"role": "assistant", "content": answer})
    chat_bubble("assistant", answer)

    # [+] UX Fix: The chat_input is disabled after submission until the next rerun.
    # A user couldn't send a follow-up message without a manual browser refresh.
    # st.rerun() clears the submitted value from the input widget and re-enables it,
    # providing a smooth, continuous chat experience.
    st.rerun()
