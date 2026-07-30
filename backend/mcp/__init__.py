"""Model Context Protocol (MCP) integration layer.

Provides a lightweight client-server abstraction for connecting external tools,
data sources, and services to the agent runtime using the MCP standard
(JSON-RPC 2.0 over STDIO or HTTP/SSE).

Design goals:
* No hard dependency on the official ``mcp`` SDK — we implement the wire
  protocol with ``httpx`` (already required) so the platform stays portable.
* Tools, Resources, and Prompts are first-class primitives that the agent
  runtime can discover and invoke dynamically.
* Graceful degradation: if no MCP servers are configured, the layer is inert.
"""

from backend.mcp.client import MCPClient, MCPClientError
from backend.mcp.registry import MCPServerConfig, mcp_registry

__all__ = ["MCPClient", "MCPClientError", "MCPServerConfig", "mcp_registry"]
