"""Registry of configured MCP servers.

Servers are declared via environment variables or a JSON config file and
lazily instantiated on first use. This keeps the runtime lightweight when no
MCP servers are configured.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from backend.mcp.client import MCPClient


@dataclass
class MCPServerConfig:
    name: str
    transport: str = "http"
    url: str | None = None
    command: str | None = None
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    enabled: bool = True


class MCPRegistry:
    """Holds MCP server configs and manages live client connections."""

    def __init__(self) -> None:
        self._configs: dict[str, MCPServerConfig] = {}
        self._clients: dict[str, MCPClient] = {}
        self._load_defaults()

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------
    def _load_defaults(self) -> None:
        """Load servers from ``MCP_SERVERS`` env var or ``config/mcp.json``."""
        env_json = os.environ.get("MCP_SERVERS")
        if env_json:
            try:
                self._load_from_list(json.loads(env_json))
            except (json.JSONDecodeError, TypeError):
                pass
        config_path = Path("config/mcp.json")
        if config_path.exists():
            try:
                data = json.loads(config_path.read_text(encoding="utf-8"))
                self._load_from_list(data.get("servers", []))
            except (json.JSONDecodeError, OSError):
                pass

    def _load_from_list(self, servers: list[dict[str, Any]]) -> None:
        for entry in servers:
            name = entry.get("name")
            if not name:
                continue
            self._configs[name] = MCPServerConfig(
                name=name,
                transport=entry.get("transport", "http"),
                url=entry.get("url"),
                command=entry.get("command"),
                args=entry.get("args", []),
                env=entry.get("env", {}),
                headers=entry.get("headers", {}),
                enabled=entry.get("enabled", True),
            )

    def register(self, config: MCPServerConfig) -> None:
        self._configs[config.name] = config

    def list_servers(self) -> list[dict[str, Any]]:
        return [
            {
                "name": c.name,
                "transport": c.transport,
                "url": c.url,
                "command": c.command,
                "enabled": c.enabled,
            }
            for c in self._configs.values()
        ]

    # ------------------------------------------------------------------
    # Client lifecycle
    # ------------------------------------------------------------------
    async def get_client(self, name: str) -> MCPClient:
        if name in self._clients:
            return self._clients[name]
        config = self._configs.get(name)
        if config is None or not config.enabled:
            raise KeyError(f"MCP server '{name}' is not configured or disabled")
        client = MCPClient(
            name=config.name,
            transport=config.transport,
            url=config.url,
            command=config.command,
            args=config.args,
            env=config.env,
            headers=config.headers,
        )
        await client.initialize()
        self._clients[name] = client
        return client

    async def close_all(self) -> None:
        for client in self._clients.values():
            await client.close()
        self._clients.clear()

    # ------------------------------------------------------------------
    # Aggregated discovery
    # ------------------------------------------------------------------
    async def discover_all_tools(self) -> list[dict[str, Any]]:
        """Aggregate tools from every enabled MCP server."""
        all_tools: list[dict[str, Any]] = []
        for name, config in self._configs.items():
            if not config.enabled:
                continue
            try:
                client = await self.get_client(name)
                tools = await client.list_tools()
                for tool in tools:
                    tool["_server"] = name
                    all_tools.append(tool)
            except Exception as exc:  # noqa: BLE001
                all_tools.append({"_server": name, "_error": str(exc)})
        return all_tools

    async def call_tool(self, server: str, tool: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        client = await self.get_client(server)
        return await client.call_tool(tool, arguments)


mcp_registry = MCPRegistry()
