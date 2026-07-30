"""Experiment tracking API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.memory.experiment_store import experiment_store
from backend.tracking import experiment_tracker

router = APIRouter(prefix="/tracking", tags=["tracking"])


class TrackExperimentRequest(BaseModel):
    job_id: str
    metrics: dict | None = None
    params: dict | None = None
    tags: dict | None = None


@router.get("/runs")
async def list_runs() -> dict:
    return {"experiments": [e.__dict__ for e in experiment_store.list()]}


@router.post("/track")
async def track(req: TrackExperimentRequest) -> dict:
    run = experiment_tracker.track_experiment(req.job_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Job '{req.job_id}' not found in experiment store")
    return {"run_id": run.run_id, "experiment_id": run.experiment_id, "backend": run.backend}
