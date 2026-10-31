from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.mcp.mcp_client_config import McpClientConfig
from swiss_ai_hub.core.persistence import TenantMetadataEntity

from swiss_ai_hub.agent.context.run.run_context import RunContext
from swiss_ai_hub.agent.mcp.mcp_tenant_header_unresolved_error import McpTenantHeaderUnresolvedError


class McpTenantHeaderResolver:
    """Inject the acting tenant's external id under ``McpClientConfig.forward_tenant_id_header``.

    The value is derived server-side from the user's acting tenant, never taken from the profile, so a tenant
    admin cannot point a profile at another tenant's external data. It is resolved on the entry step (which
    carries the user) and cached in the run context for the tool-execution steps, whose events carry no user.
    """

    TENANT_HEADER_VALUE_KEY = "mcp_tenant_header_value"

    @staticmethod
    async def apply(mcp_config: McpClientConfig, run_context: RunContext, user: UserIdentity | None) -> McpClientConfig:
        header_name = mcp_config.forward_tenant_id_header
        if not header_name:
            return mcp_config

        tenant_id_value = await McpTenantHeaderResolver._resolve(run_context, user)
        merged_headers = dict(mcp_config.headers or {})
        merged_headers[header_name] = tenant_id_value
        return mcp_config.model_copy(update={"headers": merged_headers})

    @staticmethod
    async def _resolve(run_context: RunContext, user: UserIdentity | None) -> str:
        cached: str | None = await run_context.get(McpTenantHeaderResolver.TENANT_HEADER_VALUE_KEY, None)
        if cached is not None:
            return cached

        if user is None or user.acting_within_tenant is None:
            raise McpTenantHeaderUnresolvedError("MCP tenant header is required but the run has no acting tenant.")

        tenant_id = user.acting_within_tenant.id
        entity = await TenantMetadataEntity.get_metadata_by_tenant_id(tenant_id)
        if entity is None or entity.lcdm_tenant_id is None:
            raise McpTenantHeaderUnresolvedError(
                f"MCP tenant header is required but tenant '{tenant_id}' has no external tenant id."
            )

        tenant_id_value = str(entity.lcdm_tenant_id)
        await run_context.set(McpTenantHeaderResolver.TENANT_HEADER_VALUE_KEY, tenant_id_value)
        return tenant_id_value
