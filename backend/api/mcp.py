"""MCP management API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.mcp.registry import mcp_registry
from backend.tools.registry import tool_registry

router = APIRouter(prefix="/mcp", tags=["mcp"])


class CallToolRequest(BaseModel):
    server: str
    tool: str
    arguments: dict | None = None


@router.get("/servers")
async def list_servers() -> dict:
    return {"servers": mcp_registry.list_servers()}


@router.get("/tools")
async def list_tools() -> dict:
    builtin = tool_registry.list_tools()
    mcp_count = await tool_registry.discover_mcp_tools()
    return {"builtin_tools": builtin, "mcp_tools_discovered": mcp_count, "all_tools": tool_registry.list_tools()}


@router.post("/call")
async def call_tool(req: CallToolRequest) -> dict:
    try:
        result = await mcp_registry.call_tool(req.server, req.tool, req.arguments or {})
        return {"result": result}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc))
