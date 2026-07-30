"""Knowledge graph API routes."""

from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.knowledge import build_knowledge_graph

router = APIRouter(prefix="/graph", tags=["graph"])


class BuildGraphRequest(BaseModel):
    dataset_id: str
    correlation_threshold: float = 0.7
    max_categorical_entities: int = 50


@router.post("/build")
async def build_graph(req: BuildGraphRequest) -> dict:
    try:
        from backend.memory.dataset_memory import dataset_memory
        from backend.tools.data_loader import read_dataset
        dataset = dataset_memory.get(req.dataset_id)
        df = await read_dataset(dataset.path)
        kg = build_knowledge_graph(df, req.correlation_threshold, req.max_categorical_entities)
        return kg.to_dict()
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Dataset '{req.dataset_id}' not found")
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/nodes")
async def list_nodes() -> dict:
    # Returns nodes from the most recently built graph (stateless endpoint)
    return {"message": "Use POST /graph/build to construct a graph first"}
