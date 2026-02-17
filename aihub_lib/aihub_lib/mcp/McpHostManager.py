import logging
from typing import Any

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from mcp.types import Tool
from opentelemetry import trace

from aihub_lib.mcp.McpHostConfig import McpConnectionConfig, McpHostConfig

logger = logging.getLogger(__name__)
tracer = trace.get_tracer("aihub.mcp")


class McpHostManager:
    """MCP Host abstraction — manages multiple Client instances.

    Per MCP spec, the Host:
    - Creates and manages Client instances (1:1 with Servers)
    - Aggregates tools from all connected Servers
    - Routes tool calls to the correct Client
    """

    def __init__(self, config: McpHostConfig) -> None:
        self._config = config
        self._clients: dict[str, Client] = {}  # type: ignore[type-arg]
        self._tools_cache: dict[str, list[Tool]] = {}
        self._connected = False

    async def connect_all(self) -> None:
        """Establish all Client connections (one per configured server)."""
        for conn in self._config.connections:
            transport = _create_transport(conn)
            client = Client(transport)
            await client.__aenter__()  # type: ignore[no-untyped-call]
            self._clients[conn.name] = client
            logger.info("MCP Client '%s' connected to %s", conn.name, conn.url)
        self._connected = True

    async def disconnect_all(self) -> None:
        """Close all Client connections."""
        for name, client in self._clients.items():
            try:
                await client.__aexit__(None, None, None)  # type: ignore[no-untyped-call]
                logger.info("MCP Client '%s' disconnected", name)
            except Exception:
                logger.exception("Error disconnecting MCP Client '%s'", name)
        self._clients.clear()
        self._tools_cache.clear()
        self._connected = False

    async def list_all_tools(self, refresh: bool = False) -> list[Tool]:
        """Aggregate tools from all connected Servers."""
        all_tools: list[Tool] = []
        with tracer.start_as_current_span("mcp.tool.discovery"):
            for name, client in self._clients.items():
                if refresh or name not in self._tools_cache:
                    tools = await client.list_tools()
                    self._tools_cache[name] = tools
                    logger.debug("Discovered %d tools from '%s'", len(tools), name)
                all_tools.extend(self._tools_cache[name])
        return all_tools

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Route a tool call to the correct Client and trace with OTEL."""
        conn_name = self._find_connection_for_tool(tool_name)
        client = self._clients[conn_name]

        with tracer.start_as_current_span(
            f"mcp.tool.{tool_name}",
            attributes={
                "mcp.tool.name": tool_name,
                "mcp.connection": conn_name,
            },
        ):
            logger.debug("Calling MCP tool '%s' via connection '%s'", tool_name, conn_name)
            return await client.call_tool(tool_name, arguments)

    def _find_connection_for_tool(self, tool_name: str) -> str:
        """Find which connection owns a tool (by searching the cache)."""
        for conn_name, tools in self._tools_cache.items():
            if any(t.name == tool_name for t in tools):
                return conn_name
        raise ValueError(f"Tool '{tool_name}' not found in any connected MCP server")

    @property
    def is_connected(self) -> bool:
        return self._connected


def _create_transport(conn: McpConnectionConfig) -> StreamableHttpTransport:
    """Create the appropriate transport for a connection."""
    headers: dict[str, str] = dict(conn.headers or {})
    if conn.api_key:
        headers["Authorization"] = f"Bearer {conn.api_key.get_secret_value()}"
    return StreamableHttpTransport(url=conn.url, headers=headers)
