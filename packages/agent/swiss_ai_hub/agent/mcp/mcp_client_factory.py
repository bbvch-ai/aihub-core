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

        The bearer is chosen by ``config.auth_mode``: ``none`` sends no credentials, ``api_key``
        uses ``config.api_key``, and ``user_token`` uses ``user_token`` (resolved by the caller
        from RunContext via ``McpAuthResolver``) so external actions are attributed to the
        requesting user.
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
        """Pick the bearer for the connection's auth_mode, failing loudly on a misconfigured mode."""
        match config.auth_mode:
            case "none":
                return None
            case "api_key":
                if not config.api_key:
                    msg = (
                        f"MCP connection {config.name!r} is configured with auth_mode='api_key' but no API key is set."
                    )
                    raise ValueError(msg)
                return BearerAuth(config.api_key)
            case "user_token":
                if not user_token:
                    msg = (
                        f"MCP connection {config.name!r} is configured with auth_mode='user_token' "
                        "but no user token was provided to McpClientFactory.create()."
                    )
                    raise ValueError(msg)
                return BearerAuth(user_token)
