from unittest.mock import AsyncMock, MagicMock

import pytest
from swiss_ai_hub.core.mcp.mcp_client_config import McpClientConfig
from swiss_ai_hub.core.persistence import TenantMetadataEntity
from swiss_ai_hub.core.testing.auth_utils.test_identity import fake_user

from swiss_ai_hub.agent.context.run.run_context import RunContext
from swiss_ai_hub.agent.mcp.mcp_tenant_header_resolver import McpTenantHeaderResolver
from swiss_ai_hub.agent.mcp.mcp_tenant_header_unresolved_error import McpTenantHeaderUnresolvedError

HEADER = "X-LCDM-Tenant"


def _config(forward: str | None = HEADER) -> McpClientConfig:
    return McpClientConfig(
        name="lcdm",
        url="http://mcp:9000/mcp",
        auth_mode="none",
        headers={"X-Static": "1"},
        forward_tenant_id_header=forward,
    )


def _run_context(cached: str | None = None) -> AsyncMock:
    run_context = AsyncMock(spec=RunContext)
    run_context.get = AsyncMock(return_value=cached)
    return run_context


def _stub_tenant(monkeypatch: pytest.MonkeyPatch, lcdm_tenant_id: int | None) -> None:
    entity = MagicMock(lcdm_tenant_id=lcdm_tenant_id)
    monkeypatch.setattr(TenantMetadataEntity, "get_metadata_by_tenant_id", lambda tenant_id: entity)


class TestApply:
    """A profile that forwards a tenant header must never reach the MCP server without it."""

    @pytest.mark.asyncio
    async def test_is_a_no_op_when_not_configured(self):
        config = _config(forward=None)

        assert await McpTenantHeaderResolver.apply(config, _run_context(), None) is config

    @pytest.mark.asyncio
    async def test_resolves_the_acting_tenants_external_id_and_caches_it(self, monkeypatch):
        _stub_tenant(monkeypatch, lcdm_tenant_id=5)
        run_context = _run_context()

        result = await McpTenantHeaderResolver.apply(_config(), run_context, fake_user())

        assert result.headers == {"X-Static": "1", HEADER: "5"}
        run_context.set.assert_awaited_once_with(McpTenantHeaderResolver.TENANT_HEADER_VALUE_KEY, "5")

    @pytest.mark.asyncio
    async def test_tool_steps_without_a_user_reuse_the_cached_value(self):
        result = await McpTenantHeaderResolver.apply(_config(), _run_context(cached="5"), None)

        assert result.headers[HEADER] == "5"

    @pytest.mark.asyncio
    async def test_overrides_a_static_header_of_the_same_name(self, monkeypatch):
        """A profile cannot pin another tenant's id via the static headers."""
        _stub_tenant(monkeypatch, lcdm_tenant_id=5)
        config = _config().model_copy(update={"headers": {HEADER: "999"}})

        result = await McpTenantHeaderResolver.apply(config, _run_context(), fake_user())

        assert result.headers[HEADER] == "5"

    @pytest.mark.asyncio
    async def test_fails_for_a_run_without_a_user(self):
        """Scheduled, process and bot runs carry no acting tenant."""
        with pytest.raises(McpTenantHeaderUnresolvedError):
            await McpTenantHeaderResolver.apply(_config(), _run_context(), None)

    @pytest.mark.asyncio
    async def test_fails_for_a_tenant_without_an_external_id(self, monkeypatch):
        _stub_tenant(monkeypatch, lcdm_tenant_id=None)

        with pytest.raises(McpTenantHeaderUnresolvedError):
            await McpTenantHeaderResolver.apply(_config(), _run_context(), fake_user())
