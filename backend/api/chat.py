from __future__ import annotations

import json

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from backend.llm import get_llm
from backend.memory.experiment_store import experiment_store


router = APIRouter(prefix="/chat", tags=["chat"])

_SYSTEM = (
    "You are the Advisor, an experiment-aware data-science assistant. Answer the "
    "user's question using ONLY the provided experiment context. Be concise and "
    "actionable. If the context does not cover the question, say so plainly."
)


class ChatRequest(BaseModel):
    job_id: str | None = None
    message: str


@router.post("")
async def chat(request: ChatRequest) -> dict:
    if not request.job_id:
        return {"answer": "Upload a dataset and start an agent run to receive experiment-aware guidance."}
    try:
        experiment = experiment_store.by_job(request.job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found.") from exc

    if experiment.status != "completed":
        return {"answer": f"The run is currently {experiment.status}. Watch the live reasoning stream for progress."}

    context = {
        "model": experiment.selected_model,
        "metrics": experiment.metrics,
        "features": experiment.selected_features,
        "insights": experiment.insights,
        "feature_importance": experiment.feature_importance,
    }
    llm = get_llm()
    if llm is not None:
        answer = await llm.complete(
            f"Experiment context: {json.dumps(context)}\n\nUser question: {request.message}",
            system=_SYSTEM,
            temperature=0.3,
            max_tokens=1000,
        )
        if answer:
            return {"answer": answer, "llm": True}

    # Deterministic fallback.
    best_metric = max(experiment.metrics.items(), key=lambda item: item[1], default=("score", 0))
    return {
        "answer": (
            f"The selected model is {experiment.selected_model}. "
            f"Best tracked metric is {best_metric[0]}={best_metric[1]:.3f}. "
            f"Top recommendation: {experiment.insights[0] if experiment.insights else 'Review feature quality and rerun.'}"
        ),
        "llm": False,
    }
