"""Enhanced unified tool registry.

Aggregates callable tools from three sources:
1. **Built-in tools** — existing functions in ``backend.tools.*``.
2. **MCP-discovered tools** — fetched lazily from ``mcp_registry``.
3. **Python callables** — registered dynamically at runtime.

Each tool is described with a JSON-schema-compatible input spec so the agent
runtime (or an LLM function-calling layer) can select and invoke tools
autonomously.
"""

from __future__ import annotations

import asyncio
import inspect
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable

from backend.mcp.registry import mcp_registry


@dataclass
class ToolSpec:
    name: str
    description: str
    source: str  # "builtin" | "mcp:<server>" | "python"
    input_schema: dict[str, Any] = field(default_factory=dict)
    callable: Callable[..., Any] | None = None
    mcp_server: str | None = None
    is_async: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "source": self.source,
            "input_schema": self.input_schema,
        }


class ToolRegistry:
    """Unified registry of agent-callable tools."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}
        self._register_builtins()

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------
    def register(
        self,
        name: str,
        description: str,
        func: Callable[..., Any],
        input_schema: dict[str, Any] | None = None,
    ) -> None:
        is_async = asyncio.iscoroutinefunction(func)
        self._tools[name] = ToolSpec(
            name=name,
            description=description,
            source="python",
            input_schema=input_schema or {},
            callable=func,
            is_async=is_async,
        )

    def register_builtin(self, spec: ToolSpec) -> None:
        self._tools[spec.name] = spec

    def _register_builtins(self) -> None:
        """Register existing backend.tools functions as agent tools."""
        try:
            from backend.tools.data_sources import available_samples, _sample_dataframe
            self.register(
                "list_sample_datasets",
                "List built-in sample datasets available for analysis.",
                lambda: available_samples(),
                input_schema={},
            )
            self.register(
                "load_sample_dataset",
                "Load a sample dataset by name.",
                lambda name: _sample_dataframe(name),
                input_schema={"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
            )
        except Exception:  # noqa: BLE001
            pass

        try:
            from backend.tools.data_loader import load_dataframe
            self.register(
                "load_dataframe",
                "Load a DataFrame from a dataset_id stored in dataset memory.",
                lambda dataset_id: load_dataframe(dataset_id),
                input_schema={"type": "object", "properties": {"dataset_id": {"type": "string"}}, "required": ["dataset_id"]},
            )
        except Exception:  # noqa: BLE001
            pass

        try:
            from backend.tools.domain_detection import detect_domain
            self.register(
                "detect_domain",
                "Detect the business domain of a dataset.",
                lambda df: detect_domain(df),
                input_schema={"type": "object", "properties": {"df": {"type": "object"}}, "required": ["df"]},
            )
        except Exception:  # noqa: BLE001
            pass

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------
    def list_tools(self) -> list[dict[str, Any]]:
        return [t.to_dict() for t in self._tools.values()]

    async def discover_mcp_tools(self) -> int:
        """Pull tools from all configured MCP servers. Returns count added."""
        try:
            mcp_tools = await mcp_registry.discover_all_tools()
        except Exception:  # noqa: BLE001
            return 0
        count = 0
        for tool in mcp_tools:
            if "_error" in tool:
                continue
            name = tool.get("name")
            if not name:
                continue
            server = tool.get("_server", "mcp")
            self._tools[f"mcp.{server}.{name}"] = ToolSpec(
                name=name,
                description=tool.get("description", ""),
                source=f"mcp:{server}",
                input_schema=tool.get("inputSchema", {}),
                mcp_server=server,
            )
            count += 1
        return count

    # ------------------------------------------------------------------
    # Invocation
    # ------------------------------------------------------------------
    async def call(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        arguments = arguments or {}
        tool = self._tools.get(name)
        if tool is None:
            raise KeyError(f"Tool '{name}' not found in registry")
        if tool.mcp_server:
            return await mcp_registry.call_tool(tool.mcp_server, tool.name, arguments)
        if tool.callable is None:
            raise RuntimeError(f"Tool '{name}' has no callable")
        if tool.is_async:
            return await tool.callable(**arguments)
        result = tool.callable(**arguments)
        if inspect.isawaitable(result):
            return await result
        return result

    def get_tool(self, name: str) -> ToolSpec | None:
        return self._tools.get(name)

    def to_openai_functions(self) -> list[dict[str, Any]]:
        """Export specs in OpenAI function-calling format."""
        functions = []
        for tool in self._tools.values():
            functions.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.input_schema or {"type": "object", "properties": {}},
            })
        return functions


tool_registry = ToolRegistry()
