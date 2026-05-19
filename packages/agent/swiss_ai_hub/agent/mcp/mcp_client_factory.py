from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastmcp import Client
from fastmcp.client.auth import BearerAuth
from fastmcp.client.transports import StreamableHttpTransport
from swiss_ai_hub.core.mcp.mcp_client_config import McpClientConfig


class McpClientFactory:
    """Creates FastMCP clients from McpClientConfig — used inside agent steps for per-step lifecycle."""

    @staticmethod
    @asynccontextmanager
    async def create(config: McpClientConfig, user_token: str | None = None) -> AsyncIterator[Client]:
        """Create and connect a FastMCP Client, yielding it for use within an async with block.

        When ``config.auth_mode == "user_token"``, the bearer is taken from ``user_token`` (resolved
        by the caller from RunContext via ``McpAuthResolver``) so external actions are attributed to
        the requesting user. The default ``static_api_key`` mode uses ``config.api_key``.
        """
        auth = McpClientFactory._resolve_auth(config, user_token)

        if config.headers:
            transport = StreamableHttpTransport(url=config.url, headers=dict(config.headers), auth=auth)
            client = Client(transport, name=config.name, timeout=config.timeout)
        else:
            client = Client(config.url, name=config.name, timeout=config.timeout, auth=auth)

        async with client:
            yield client

    @staticmethod
    def _resolve_auth(config: McpClientConfig, user_token: str | None) -> BearerAuth | None:
        if config.auth_mode == "user_token":
            if not user_token:
                msg = (
                    f"MCP connection {config.name!r} is configured with auth_mode='user_token' "
                    "but no user token was provided to McpClientFactory.create()."
                )
                raise ValueError(msg)
            return BearerAuth(user_token)
        return BearerAuth(config.api_key) if config.api_key else None
