from __future__ import annotations
import asyncio
import logging
import time
import uuid
from typing import Any, TypedDict
from fastapi import APIRouter, HTTPException
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent/jobs", tags=["jobs"])
class JobResponse(TypedDict):
    """Standardized job response format"""
    job_id: str
    status: str
    created_at: float
    ttl: float
    stages: list[dict[str, Any]]
class _JobStoreEntry(TypedDict):
    """Job metadata with type hints"""
    job_id: str
    status: str
    created_at: float
    ttl: float
    stages: list[dict[str, Any]]
# In-memory store - in a real system this would be a database or a
# distributed cache. Not shared across multiple Uvicorn workers.
_jobs: dict[str, _JobStoreEntry] = {}
_jobs_lock = asyncio.Lock()
# Remove jobs older than 1 hour to prevent unbounded memory growth.
_JOB_TTL_SECONDS = 3600
async def _cleanup_stale_jobs() -> None:
    """Remove jobs that have exceeded the TTL."""
    cutoff = time.time() - _JOB_TTL_SECONDS
    stale = [
        job_id
        for job_id, job in _jobs.items()
        if job.get("created_at", 0.0) < cutoff
    ]
    for job_id in stale:
        _jobs.pop(job_id, None)
        logger.debug("Removed stale job %s", job_id)
@router.post("/", response_model=JobResponse)
async def create_job() -> JobResponse:
    """Create a new job and return its UUID.
    The job is added to the in-memory store with a default status of ``queued``.
    The response contains only the ``job_id``; the UI can query ``/agent/jobs/{job_id}``
    for status updates.
    """
    async with _jobs_lock:
        await _cleanup_stale_jobs()
        job_id = str(uuid.uuid4())
        _jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "stages": [],
            "created_at": time.time(),
            "ttl": _JOB_TTL_SECONDS,
        }
        logger.info("Created job %s", job_id)
        return JobResponse(job_id=job_id, status=_jobs[job_id]["status"], created_at=_jobs[job_id]["created_at"], ttl=_jobs[job_id]["ttl"], stages=_jobs[job_id]["stages"])
@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str) -> JobResponse:
    """Return the stored job data.
    Raises a 404 if the job does not exist or has expired.
    """
    try:
        uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid job ID format: {job_id}",
        )
    async with _jobs_lock:
        job = _jobs.get(job_id)
        if not job:
            logger.warning("Job not found: %s", job_id)
            raise HTTPException(
                status_code=404,
                detail=f"Job not found: {job_id}",
            )
        # Clean up if expired
        if time.time() - job.get("created_at", 0.0) > _JOB_TTL_SECONDS:
            _jobs.pop(job_id, None)
            logger.info("Expired job removed: %s", job_id)
            raise HTTPException(
                status_code=404,
                detail=f"Job expired: {job_id}",
            )
        return JobResponse(job_id=job["job_id"], status=job["status"], created_at=job["created_at"], ttl=job["ttl"], stages=job["stages"])
"""Job creation and status endpoints.
This module provides a minimal in-memory job store used by the Streamlit *Intelligence* page.
The backend does not persist jobs to disk - the goal is to give the UI a stable identifier that can be copied into the event-stream filter.
The implementation is intentionally lightweight: a UUID is generated, stored in a module-level dictionary, and returned to the caller.
A ``GET`` route returns the stored job data, which the UI can use to display status.
Note: The in-memory store is not shared across multiple Uvicorn workers.
For production deployments, replace ``_jobs`` with a database or distributed cache (e.g., Redis).
"""

__all__ = ["router"]
