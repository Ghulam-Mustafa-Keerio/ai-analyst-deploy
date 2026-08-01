from __future__ import annotations

import logging
import streamlit as st
import httpx

from ui.components.chat_bubble import chat_bubble
from ui.components.feedback import empty_state
from ui.components.plot_3d import scatter_3d
from ui.services import api_client

logger = logging.getLogger(__name__)

st.markdown(
    """
<style>
/* ── Advisor page styles ── */
.advisor-container {
    max-width: 900px;
    margin: 0 auto;
}

/* ── Suggestion chips ── */
.suggestion-chip {
    display: inline-block;
    padding: 8px 16px;
    margin: 4px 6px 4px 0;
    border-radius: 999px;
    font-size: 0.82rem;
    font-weight: 500;
    color: #60a5fa;
    background: rgba(37, 99, 235, 0.1);
    border: 1px solid rgba(96, 165, 250, 0.25);
    cursor: pointer;
    transition: all 0.2s ease;
    text-decoration: none;
}
.suggestion-chip:hover {
    background: rgba(37, 99, 235, 0.2);
    border-color: rgba(96, 165, 250, 0.5);
    color: #93c5fd;
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.2);
}

/* ── Decision framework card ── */
.decision-card {
    background: rgba(30, 41, 59, 0.6);
    border: 1px solid rgba(148, 163, 184, 0.15);
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 16px;
    backdrop-filter: blur(12px);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}
.decision-card .label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #94a3b8;
    margin-bottom: 8px;
}
.decision-card .value {
    font-size: 1rem;
    font-weight: 600;
    color: #f8fafc;
}

/* ── Chat input styling ── */
[data-testid="stChatInput"] {
    border-radius: 12px;
    overflow: hidden;
}
[data-testid="stChatInput"] textarea {
    background: rgba(30, 41, 59, 0.8) !important;
    border: 1px solid rgba(148, 163, 184, 0.2) !important;
    border-radius: 12px !important;
    color: #f8fafc !important;
    font-size: 0.9rem !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: rgba(96, 165, 250, 0.5) !important;
    box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.15) !important;
}

/* ── 3D context expander ── */
.streamlit-expander {
    background: rgba(30, 41, 59, 0.4) !important;
    border: 1px solid rgba(148, 163, 184, 0.15) !important;
    border-radius: 12px !important;
    overflow: hidden;
}
</style>
""",
    unsafe_allow_html=True,
)


def render_advisor() -> None:
    st.markdown('<div class="eyebrow">Workspace / Advisor</div>', unsafe_allow_html=True)
    st.title("Advisor")
    st.caption("Experiment-aware guidance grounded in the active agent run.")

    st.session_state.setdefault("advisor_messages", [])

    if not st.session_state.get("job_id"):
        empty_state(
            "💬",
            "No active run to advise on",
            "Start an agent run from the Dashboard, then return here to ask about model choice, metrics, features, or next experiments.",
        )
        return

    # ── Suggestion prompts ──
    suggestions = [
        "Which model performed best?",
        "What features matter most?",
        "How can I improve accuracy?",
        "What should I try next?",
    ]
    st.markdown('<div class="advisor-container">', unsafe_allow_html=True)
    st.markdown(
        '<div style="margin-bottom: 1rem;">'
        + "".join(f'<span class="suggestion-chip">{s}</span>' for s in suggestions)
        + "</div>",
        unsafe_allow_html=True,
    )

    dataset = st.session_state.get("dataset")
    if dataset:
        with st.expander("3D dataset context", expanded=False):
            st.caption("PCA projection of the active dataset, grounding the advisor's reasoning.")
            try:
                embedding = api_client.run(api_client.embed_3d(st.session_state.api_base_url, dataset.get("dataset_id")))
                scatter_3d(embedding.get("points", []), color="#60a5fa")
            except httpx.HTTPStatusError as exc:
                st.info(f"3D context unavailable: {exc}")

    for message in st.session_state.advisor_messages:
        chat_bubble(message["role"], message["content"])

    st.markdown('</div>', unsafe_allow_html=True)

    prompt = st.chat_input("Ask about model choice, metrics, features, or next experiments")
    if not prompt:
        return

    st.session_state.advisor_messages.append({"role": "user", "content": prompt})
    chat_bubble("user", prompt)

    with st.spinner("Advisor is thinking…"):
        try:
            response = api_client.run(api_client.chat(st.session_state.api_base_url, job_id=st.session_state.job_id, message=prompt))
            # Reliability: Use .get() for safe access. If the "answer" key is missing,
            # this prevents a KeyError and provides a graceful fallback message.
            answer = response.get("answer", "I'm sorry, I encountered an issue and couldn't form a response.")
        except httpx.ConnectError:
            answer = "Unable to reach the advisor: Connection failed. Please check the backend server."
        except httpx.HTTPStatusError as exc:
            answer = f"Unable to reach the advisor: Server returned status {exc.response.status_code}."
        except Exception as exc:
            logger.error(f"Advisor chat failed unexpectedly: {exc}", exc_info=True)
            # UX/Security: Show a generic error to the user instead of leaking implementation details.
            # The full error is logged for debugging.
            answer = "An unexpected error occurred. Please check the logs for more details."

    st.session_state.advisor_messages.append({"role": "assistant", "content": answer})
    chat_bubble("assistant", answer)

    # UX Fix: The chat_input is disabled after submission until the next rerun.
    # A user couldn't send a follow-up message without a manual browser refresh.
    # st.rerun() clears the submitted value from the input widget and re-enables it,
    # providing a smooth, continuous chat experience.
    st.rerun()
