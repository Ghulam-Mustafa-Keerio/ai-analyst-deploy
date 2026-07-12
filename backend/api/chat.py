from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from backend.memory.experiment_store import experiment_store


router = APIRouter(prefix="/chat", tags=["chat"])


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
    best_metric = max(experiment.metrics.items(), key=lambda item: item[1], default=("score", 0))
    return {
        "answer": (
            f"The selected model is {experiment.selected_model}. "
            f"Best tracked metric is {best_metric[0]}={best_metric[1]:.3f}. "
            f"Top recommendation: {experiment.insights[0] if experiment.insights else 'Review feature quality and rerun.'}"
        )
    }
