from __future__ import annotations

import asyncio
from dataclasses import asdict
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.memory.dataset_memory import dataset_memory
from backend.tools.data_loader import profile_dataset


import os

router = APIRouter(prefix="/upload", tags=["upload"])
UPLOAD_DIR = Path("/tmp/data/uploads") if os.environ.get("VERCEL") else Path("data/uploads")

# Vercel serverless functions cap the request body (~4.5 MB). Reject larger
# uploads early with a clear error instead of a generic 413.
MAX_UPLOAD_BYTES = 4 * 1024 * 1024


@router.post("")
async def upload_dataset(file: UploadFile = File(...)) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required.")
    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".csv", ".parquet"}:
        raise HTTPException(status_code=400, detail="Only CSV and Parquet datasets are supported.")

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Dataset is too large ({len(content) / 1024 / 1024:.1f} MB). "
            f"Serverless deployments accept up to 4 MB. Use a smaller sample or self-host the backend.",
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename).name.replace(" ", "_")
    path = UPLOAD_DIR / f"{uuid4().hex}_{safe_name}"
    content = await file.read()
    await asyncio.to_thread(path.write_bytes, content)
    from backend.tools.domain_detection import detect_domain
    profile = await profile_dataset(path)
    profile["domain"] = detect_domain(list(profile["schema"]))
    record = dataset_memory.register(
        filename=file.filename,
        path=path,
        rows=profile["rows"],
        columns=profile["columns"],
        schema=profile["schema"],
    )
    return {"dataset": asdict(record), "profile": profile}


@router.get("/datasets")
async def list_datasets() -> dict:
    return {"datasets": dataset_memory.list()}
