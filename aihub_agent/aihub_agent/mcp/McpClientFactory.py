from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from aihub_lib.mcp.McpClientConfig import McpClientConfig
from fastmcp import Client
from fastmcp.client.auth import BearerAuth
from fastmcp.client.transports import StreamableHttpTransport


class McpClientFactory:
    """Creates FastMCP clients from McpClientConfig — used inside agent steps for per-step lifecycle."""

    @staticmethod
    @asynccontextmanager
    async def create(config: McpClientConfig) -> AsyncIterator[Client]:
        """Create and connect a FastMCP Client, yielding it for use within an async with block."""
        auth = BearerAuth(config.api_key.get_secret_value()) if config.api_key else None

        if config.headers:
            transport = StreamableHttpTransport(url=config.url, headers=dict(config.headers), auth=auth)
            client = Client(transport, name=config.name, timeout=config.timeout)
        else:
            client = Client(config.url, name=config.name, timeout=config.timeout, auth=auth)

        async with client:
            yield client
