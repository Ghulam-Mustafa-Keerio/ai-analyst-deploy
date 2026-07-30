"""BI connector API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.integrations.bi import powerbi_connector, dbt_connector

router = APIRouter(prefix="/bi", tags=["bi"])


class PushRowsRequest(BaseModel):
    dataset_id: str
    table_name: str
    rows: list[dict]


@router.get("/powerbi/datasets")
async def pbi_datasets() -> dict:
    if not powerbi_connector.configured:
        return {"configured": False, "message": "Power BI credentials not set"}
    try:
        datasets = await powerbi_connector.list_datasets()
        return {"configured": True, "datasets": datasets}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/powerbi/push")
async def pbi_push(req: PushRowsRequest) -> dict:
    if not powerbi_connector.configured:
        raise HTTPException(status_code=400, detail="Power BI not configured")
    try:
        result = await powerbi_connector.push_rows(req.dataset_id, req.table_name, req.rows)
        return {"result": result}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/dbt/run")
async def dbt_run(select: str | None = None) -> dict:
    if dbt_connector.mode == "none":
        raise HTTPException(status_code=400, detail="dbt not configured")
    try:
        if dbt_connector.mode == "cloud":
            result = await dbt_connector.trigger_cloud_run()
        else:
            result = dbt_connector.run_local(select=select)
        return {"result": result}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc))
