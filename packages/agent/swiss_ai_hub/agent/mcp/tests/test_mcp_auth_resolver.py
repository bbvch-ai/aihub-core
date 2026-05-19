from unittest.mock import AsyncMock

import pytest

from swiss_ai_hub.agent.context.run.run_context import RunContext
from swiss_ai_hub.agent.mcp.mcp_auth_resolver import McpAuthResolver


class TestResolveUserToken:
    """The resolver is the MCP-side read of the X-AIHub-* headers contract from #948.

    Writer side lives in AgentDispatcher (PR #1258). The two constants on the resolver
    (AIHUB_HEADERS_KEY, USER_TOKEN_HEADER) must stay in lockstep with the dispatcher writer
    and NATSMessageHeaders.extract_aihub_headers — drift will make user_token MCP auth
    silently break.
    """

    @pytest.mark.asyncio
    async def test_returns_token_when_header_present(self):
        run_context = AsyncMock(spec=RunContext)
        run_context.get = AsyncMock(return_value={McpAuthResolver.USER_TOKEN_HEADER: "user-token-abc"})

        token = await McpAuthResolver.resolve_user_token(run_context)

        assert token == "user-token-abc"
        run_context.get.assert_awaited_once_with(McpAuthResolver.AIHUB_HEADERS_KEY)

    @pytest.mark.asyncio
    async def test_returns_none_when_no_headers_in_run_context(self):
        """Normal case for runs initiated outside an HTTP request (scheduled, process-initiated)."""
        run_context = AsyncMock(spec=RunContext)
        run_context.get = AsyncMock(return_value=None)

        assert await McpAuthResolver.resolve_user_token(run_context) is None

    @pytest.mark.asyncio
    async def test_returns_none_when_headers_dict_is_empty(self):
        run_context = AsyncMock(spec=RunContext)
        run_context.get = AsyncMock(return_value={})

        assert await McpAuthResolver.resolve_user_token(run_context) is None

    @pytest.mark.asyncio
    async def test_returns_none_when_other_aihub_headers_present_but_no_user_token(self):
        """Don't synthesize a token from unrelated identity headers — fail clean instead."""
        run_context = AsyncMock(spec=RunContext)
        run_context.get = AsyncMock(return_value={"x-aihub-tenant-id": "acme"})

        assert await McpAuthResolver.resolve_user_token(run_context) is None
