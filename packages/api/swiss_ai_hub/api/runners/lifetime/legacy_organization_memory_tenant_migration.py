from typing import Any

from swiss_ai_hub.core.generative_ai import OrganizationMemory
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.persistence import AgentConfigEntityDocument


class LegacyOrganizationMemoryTenantMigration:
    """Moves organization memory and the profiles that address it off the platform-wide `AIHub` owner.

    Organization memory used to be read and edited through one owner shared by every tenant, and agent profiles
    seeded from code defaulted to the same owner. Both now belong to a real tenant, so whatever was stored under the
    shared owner is handed to the startup tenant, the only tenant that existed while that owner was in use.
    Idempotent: once nothing is stored under the legacy owner, every later start rewrites nothing.
    """

    LEGACY_TENANT_ID = "AIHub"

    def __init__(self, startup_tenant_id: str):
        self._startup_tenant_id = startup_tenant_id

    async def adopt_memories(self, t: LocaleHandler) -> int:
        """Moves every organization memory of the legacy owner to the startup tenant; returns how many moved."""
        organization_memory = OrganizationMemory(tenant_id=self._startup_tenant_id, t=t)
        return await organization_memory.adopt_memories_of(self.LEGACY_TENANT_ID)

    def retarget_profiles(self) -> list[str]:
        """Points every profile still scoped to the legacy owner at the startup tenant; returns which it rewrote."""
        migrated: list[str] = []
        for document in AgentConfigEntityDocument.find_all():
            config_data = document.config_data
            rewritten = self.rewritten(config_data)
            if rewritten != config_data and AgentConfigEntityDocument.replace_config_data_if_unchanged(
                document.pk, config_data, rewritten
            ):
                migrated.append(f"agent {document.agent_class}/{document.agent_id}")
        return migrated

    def rewritten(self, value: Any) -> Any:
        """A copy of `value` whose organization-memory scopes on the legacy owner name the startup tenant."""
        if isinstance(value, list):
            return [self.rewritten(item) for item in value]
        if not isinstance(value, dict):
            return value
        rewritten = {key: self.rewritten(item) for key, item in value.items()}
        if self._is_legacy_org_memory_scope(rewritten):
            rewritten["tenant_id"] = self._startup_tenant_id
        return rewritten

    def _is_legacy_org_memory_scope(self, value: dict[str, Any]) -> bool:
        """Keyed on `allowed_tenant_namespaces` because other configs (mail, Teams) carry an unrelated `tenant_id`."""
        return "allowed_tenant_namespaces" in value and value.get("tenant_id") == self.LEGACY_TENANT_ID
