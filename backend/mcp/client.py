"""Minimal MCP client implementing the JSON-RPC 2.0 wire protocol.

Supports two transports:
* ``http``  — POST JSON-RPC to a remote MCP server (SSE stream optional).
* ``stdio`` — spawn a local process and communicate over stdin/stdout.

The client exposes the three MCP primitives:
* ``list_tools()``      -> discover callable tools.
* ``call_tool(name, args)`` -> invoke a tool and return its result.
* ``list_resources()``  -> discover readable resources.
* ``read_resource(uri)``    -> fetch resource content.
* ``list_prompts()``    -> discover prompt templates.
* ``get_prompt(name, args)`` -> render a prompt template.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any

import httpx

JSONRPC_VERSION = "2.0"


class MCPClientError(RuntimeError):
    """Raised when an MCP server returns an error or is unreachable."""


@dataclass
class MCPClient:
    """A single MCP server connection."""

    name: str
    transport: str = "http"  # "http" | "stdio"
    url: str | None = None
    command: str | None = None
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    timeout: float = 30.0
    _process: asyncio.subprocess.Process | None = field(default=None, init=False, repr=False)
    _request_id: int = field(default=0, init=False, repr=False)
    _initialized: bool = field(default=False, init=False, repr=False)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    async def initialize(self) -> dict[str, Any]:
        """Perform the MCP handshake (initialize -> initialized)."""
        if self._initialized:
            return {"status": "already_initialized"}
        result = await self._rpc("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "ai-analyst", "version": "2.1.0"},
        })
        await self._notify("notifications/initialized", {})
        self._initialized = True
        return result

    async def close(self) -> None:
        if self._process is not None:
            try:
                self._process.terminate()
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except (ProcessLookupError, asyncio.TimeoutError):
                pass
            self._process = None
        self._initialized = False

    # ------------------------------------------------------------------
    # MCP primitives
    # ------------------------------------------------------------------
    async def list_tools(self) -> list[dict[str, Any]]:
        result = await self._rpc("tools/list", {})
        return result.get("tools", [])

    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._rpc("tools/call", {"name": name, "arguments": arguments or {}})

    async def list_resources(self) -> list[dict[str, Any]]:
        result = await self._rpc("resources/list", {})
        return result.get("resources", [])

    async def read_resource(self, uri: str) -> dict[str, Any]:
        return await self._rpc("resources/read", {"uri": uri})

    async def list_prompts(self) -> list[dict[str, Any]]:
        result = await self._rpc("prompts/list", {})
        return result.get("prompts", [])

    async def get_prompt(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._rpc("prompts/get", {"name": name, "arguments": arguments or {}})

    # ------------------------------------------------------------------
    # Transport layer
    # ------------------------------------------------------------------
    async def _rpc(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        self._request_id += 1
        payload = {
            "jsonrpc": JSONRPC_VERSION,
            "id": self._request_id,
            "method": method,
            "params": params,
        }
        if self.transport == "http":
            return await self._http_rpc(payload)
        return await self._stdio_rpc(payload)

    async def _notify(self, method: str, params: dict[str, Any]) -> None:
        payload = {"jsonrpc": JSONRPC_VERSION, "method": method, "params": params}
        if self.transport == "http":
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    await client.post(
                        f"{self.url}/notify",
                        json=payload,
                        headers=self.headers,
                    )
            except httpx.HTTPError:
                pass  # notifications are best-effort
        else:
            await self._stdio_send(payload)

    async def _http_rpc(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.url:
            raise MCPClientError(f"MCP server '{self.name}' has no url configured")
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(self.url, json=payload, headers=self.headers)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as exc:
            raise MCPClientError(f"MCP HTTP call to '{self.name}' failed: {exc}") from exc
        if "error" in data:
            raise MCPClientError(f"MCP server '{self.name}' error: {data['error']}")
        return data.get("result", {})

    async def _stdio_rpc(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self._process is None:
            await self._spawn()
        await self._stdio_send(payload)
        return await self._stdio_recv()

    async def _spawn(self) -> None:
        env = {**os.environ, **self.env}
        try:
            self._process = await asyncio.create_subprocess_exec(
                self.command or sys.executable,
                *self.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
        except OSError as exc:
            raise MCPClientError(f"Failed to spawn MCP server '{self.name}': {exc}") from exc

    async def _stdio_send(self, payload: dict[str, Any]) -> None:
        if self._process is None or self._process.stdin is None:
            raise MCPClientError(f"MCP server '{self.name}' stdin not available")
        data = (json.dumps(payload) + "\n").encode()
        self._process.stdin.write(data)
        await self._process.stdin.drain()

    async def _stdio_recv(self) -> dict[str, Any]:
        if self._process is None or self._process.stdout is None:
            raise MCPClientError(f"MCP server '{self.name}' stdout not available")
        try:
            line = await asyncio.wait_for(self._process.stdout.readline(), timeout=self.timeout)
        except asyncio.TimeoutError as exc:
            raise MCPClientError(f"MCP server '{self.name}' timed out") from exc
        if not line:
            raise MCPClientError(f"MCP server '{self.name}' closed the connection")
        try:
            data = json.loads(line.decode())
        except json.JSONDecodeError as exc:
            raise MCPClientError(f"MCP server '{self.name}' sent invalid JSON: {exc}") from exc
        if "error" in data:
            raise MCPClientError(f"MCP server '{self.name}' error: {data['error']}")
        return data.get("result", {})
