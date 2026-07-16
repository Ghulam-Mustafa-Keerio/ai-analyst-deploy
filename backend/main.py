from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Local .env secrets are loaded by backend.llm on import (stdlib-only loader).
from backend.llm import llm_available  # noqa: E402,F401  (triggers .env load)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.agent import router as agent_router
from backend.api.chat import router as chat_router
from backend.api.data_sources import router as data_sources_router
from backend.api.status_ws import router as status_ws_router
from backend.api.upload import router as upload_router


app = FastAPI(
    title="Autonomous Data Science Agent OS",
    version="2.0.0",
    description="Observable multi-agent runtime for autonomous dataset analysis and model training.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(agent_router)
app.include_router(chat_router)
app.include_router(data_sources_router)
app.include_router(status_ws_router)

@app.get("/")
async def root() -> dict:
    return {
        "message": "Autonomous Data Science Agent OS Runtime is active.",
        "documentation": "/docs",
        "health_check": "/health"
    }
@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "agent-os-v2"}
