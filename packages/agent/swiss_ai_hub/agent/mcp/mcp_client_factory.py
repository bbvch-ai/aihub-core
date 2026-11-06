import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastmcp import Client
from fastmcp.client.auth import BearerAuth
from fastmcp.client.transports import SSETransport, StreamableHttpTransport
from fastmcp.mcp_config import infer_transport_type_from_url
from swiss_ai_hub.core.mcp import McpClientConfig, McpSettings
from swiss_ai_hub.core.network import PublicHostGuard

_MCP_SDK_DEFAULT_TIMEOUT = httpx.Timeout(30.0, read=300.0)


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

        Only public hosts, or those named in ``MCP_ALLOWED_PRIVATE_HOSTS``, are connected to, and no redirect is
        followed: a profile editor sets the URL, and the agent can reach the platform's own services.
        """
        auth = McpClientFactory._resolve_auth(config, user_token)
        await asyncio.to_thread(
            PublicHostGuard.require_public,
            config.url,
            McpSettings().private_host_allow_list(),
            "MCP_ALLOWED_PRIVATE_HOSTS",
        )
        transport_type = SSETransport if infer_transport_type_from_url(config.url) == "sse" else StreamableHttpTransport
        transport = transport_type(
            url=config.url,
            headers=dict(config.headers or {}),
            auth=auth,
            httpx_client_factory=McpClientFactory._http_client_without_redirects,
        )

        async with Client(transport, name=config.name, timeout=config.timeout) as client:
            yield client

    @staticmethod
    def _http_client_without_redirects(
        headers: dict[str, str] | None = None,
        timeout: httpx.Timeout | None = None,
        auth: httpx.Auth | None = None,
        **_: object,
    ) -> httpx.AsyncClient:
        """The MCP SDK's client defaults, minus the redirects it always follows: the guard checked the configured
        host only."""
        return httpx.AsyncClient(
            headers=headers,
            timeout=timeout or _MCP_SDK_DEFAULT_TIMEOUT,
            auth=auth,
            follow_redirects=False,
        )

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
