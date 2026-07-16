from __future__ import annotations

import asyncio
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.memory.dataset_memory import dataset_memory
from backend.tools.data_loader import profile_dataset
from backend.tools.data_sources import (
    DataSourceType,
    available_samples,
    connect_sql,
    resolve_dataset,
)
from backend.tools.domain_detection import detect_domain
from backend.tools.embeddings_3d import compute_3d_embedding

router = APIRouter(prefix="/data", tags=["data-sources"])

MAX_BYTES = 4 * 1024 * 1024


class ConnectRequest(BaseModel):
    source_type: DataSourceType
    filename: str | None = None
    source_url: str | None = None
    query: str | None = None
    table: str | None = None
    sample_key: str | None = None
    data_key: str | None = None


@router.get("/samples")
async def list_samples() -> dict:
    return {"samples": available_samples()}


@router.post("/connect")
async def connect_source(request: ConnectRequest) -> dict:
    """Resolve a data source to a registered dataset and return its profile."""
    try:
        path = await resolve_dataset(
            source_type=request.source_type,
            filename=request.filename,
            source_url=request.source_url,
            query=request.query,
            table=request.table,
            sample_key=request.sample_key,
            data_key=request.data_key,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # network / DB errors
        raise HTTPException(status_code=502, detail=f"Could not connect to source: {exc}") from exc

    profile = await profile_dataset(path)
    profile["domain"] = detect_domain(list(profile["schema"]))
    record = dataset_memory.register(
        filename=request.filename or f"{request.source_type.value}_source",
        path=path,
        rows=profile["rows"],
        columns=profile["columns"],
        schema=profile["schema"],
        source_type=request.source_type.value,
    )
    return {"dataset": record.__dict__, "profile": profile}


@router.post("/sql/preview")
async def preview_sql(request: ConnectRequest) -> dict:
    """Validate a SQL connection and return available tables / a preview."""
    if request.source_type != DataSourceType.sql:
        raise HTTPException(status_code=400, detail="This endpoint is for SQL sources only.")
    try:
        return await connect_sql(request.source_url or "", query=request.query, table=request.table)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"SQL connection failed: {exc}") from exc


@router.get("/datasets/{dataset_id}/embed-3d")
async def embed_3d(dataset_id: str) -> dict:
    try:
        record = dataset_memory.get(dataset_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Dataset not found.") from exc
    return await compute_3d_embedding(record.path)
