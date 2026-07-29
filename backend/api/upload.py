from __future__ import annotations

import asyncio
from dataclasses import asdict
from pathlib import Path
import json
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.memory.dataset_memory import dataset_memory
from backend.tools.dashboard_plan import build_dashboard_plan
from backend.tools.data_loader import profile_dataset


import os

router = APIRouter(prefix="/upload", tags=["upload"])
UPLOAD_DIR = Path("/tmp/data/uploads") if os.environ.get("VERCEL") else Path("data/uploads")


def get_max_upload_bytes() -> int:
    """Return the maximum upload size for the current backend configuration.

    The limit is now configurable via a JSON file located at
    ``config/upload_limit.json``.  The file should contain a single key
    ``max_upload_mb`` with an integer value.  If the file is missing or
    malformed, the function falls back to the existing environment variable
    logic, which defaults to 4 MB.
    """
    # First try to load a JSON configuration file.
    config_path = Path("config/upload_limit.json")
    if config_path.is_file():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            mb = int(data.get("max_upload_mb", 4))
            return max(1, mb) * 1024 * 1024
        except Exception:
            # If anything goes wrong we fall back to the env var logic.
            pass
    # Fallback to environment variable or default.
    try:
        return max(1, int(os.environ.get("SERVERLESS_MAX_UPLOAD_MB", "4"))) * 1024 * 1024
    except ValueError:
        return 4 * 1024 * 1024


@router.post("")
async def upload_dataset(file: UploadFile = File(...)) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required.")
    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".csv", ".parquet", ".json", ".xls", ".xlsx"}:
        raise HTTPException(status_code=400, detail="Only CSV, Parquet, JSON, and Excel datasets are supported.")

    content = await file.read()
    max_upload_bytes = get_max_upload_bytes()
    if len(content) > max_upload_bytes:
        max_upload_mb = max_upload_bytes // (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"Dataset is too large ({len(content) / 1024 / 1024:.1f} MB). "
            f"Serverless deployments accept up to {max_upload_mb} MB. Use a smaller sample or self-host the backend.",
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename).name.replace(" ", "_")
    path = UPLOAD_DIR / f"{uuid4().hex}_{safe_name}"
    await asyncio.to_thread(path.write_bytes, content)
    from backend.tools.domain_detection import detect_domain
    profile = await profile_dataset(path)
    profile["domain"] = detect_domain(list(profile["schema"]))
    profile["dashboard"] = build_dashboard_plan(list(profile["schema"]), profile)
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
