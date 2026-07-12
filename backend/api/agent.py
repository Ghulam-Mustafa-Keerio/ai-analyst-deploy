from __future__ import annotations

import asyncio
import os
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field
from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.agents.runtime import agent_runtime
from backend.memory.dataset_memory import dataset_memory
from backend.memory.experiment_store import experiment_store
from backend.tools.data_loader import preview_dataset, profile_dataset
from backend.tools.domain_detection import available_domains, detect_domain
from backend.tools.evaluation import compare_experiments


router = APIRouter(prefix="/agent", tags=["agent"])

# On serverless platforms (Vercel) background tasks are killed when the request
# returns and in-memory state is not shared across invocations. In that mode we
# run the pipeline synchronously inside the request and return the full result.
SERVERLESS = bool(os.environ.get("VERCEL"))

UPLOAD_DIR = Path("/tmp/data/uploads") if SERVERLESS else Path("data/uploads")


class StartAgentRequest(BaseModel):
    dataset_id: str
    mode: str = Field(default="autonomous", pattern="^(manual|assisted|autonomous)$")
    target: str | None = None
    features: list[str] = Field(default_factory=list)
    model: str | None = None


@router.post("/start")
async def start_agent(request: StartAgentRequest) -> dict:
    try:
        dataset = dataset_memory.get(request.dataset_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Dataset not found.") from exc
    if SERVERLESS:
        # Run inline and return the completed job status + events in one response.
        status = await agent_runtime.run_sync(
            dataset_id=dataset.dataset_id,
            dataset_path=dataset.path,
            mode=request.mode,
            target=request.target,
            features=request.features,
            model=request.model,
        )
        return {"job_id": status["job_id"], "status": status, "stream_url": None}
    job_id = await agent_runtime.start(
        dataset_id=dataset.dataset_id,
        dataset_path=dataset.path,
        mode=request.mode,
        target=request.target,
        features=request.features,
        model=request.model,
    )
    return {"job_id": job_id, "stream_url": f"/ws/status/{job_id}"}


class RunAgentRequest(BaseModel):
    mode: str = Field(default="autonomous", pattern="^(manual|assisted|autonomous)$")
    target: str | None = None
    features: str = ""
    model: str | None = None

    @property
    def feature_list(self) -> list[str]:
        return [item.strip() for item in self.features.split(",") if item.strip()]


@router.post("/run")
async def run_agent(file: UploadFile = File(...), request: RunAgentRequest = RunAgentRequest()) -> dict:
    """Upload a dataset and run the agent pipeline in a single request.

    Required on serverless platforms where uploaded files and in-memory state do
    not persist across separate invocations. Returns the completed job status.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required.")
    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".csv", ".parquet"}:
        raise HTTPException(status_code=400, detail="Only CSV and Parquet datasets are supported.")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename).name.replace(" ", "_")
    path = UPLOAD_DIR / f"{uuid4().hex}_{safe_name}"
    content = await file.read()
    await asyncio.to_thread(path.write_bytes, content)

    profile = await profile_dataset(path)
    profile["domain"] = detect_domain(list(profile["schema"]))
    record = dataset_memory.register(
        filename=file.filename,
        path=path,
        rows=profile["rows"],
        columns=profile["columns"],
        schema=profile["schema"],
    )
    status = await agent_runtime.run_sync(
        dataset_id=record.dataset_id,
        dataset_path=record.path,
        mode=request.mode,
        target=request.target,
        features=request.feature_list,
        model=request.model,
    )
    return {"dataset": record.__dict__, "profile": profile, "job_id": status["job_id"], "status": status}


@router.get("/jobs/{job_id}")
async def get_job(job_id: str) -> dict:
    try:
        return agent_runtime.status(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found.") from exc


@router.get("/experiments")
async def list_experiments() -> dict:
    return {"experiments": experiment_store.list()}


@router.get("/domains")
async def list_domains() -> dict:
    return {"domains": available_domains()}


@router.get("/domains/{domain_name}")
async def get_domain_details(domain_name: str) -> dict:
    from pathlib import Path
    domain_root = Path("skills/business_domains")
    path = domain_root / f"{domain_name}.md"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Domain not found.")
    try:
        content = path.read_text(encoding="utf-8")
        return {"domain": domain_name, "content": content}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read domain info: {exc}")


@router.get("/experiments/compare")
async def compare_runs() -> dict:
    return {"experiments": compare_experiments(experiment_store.list())}


@router.get("/datasets/{dataset_id}/preview")
async def dataset_preview(dataset_id: str, page: int = 1, page_size: int = 100) -> dict:
    try:
        dataset = dataset_memory.get(dataset_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Dataset not found.") from exc
    return await preview_dataset(dataset.path, page=page, page_size=min(page_size, 500))
