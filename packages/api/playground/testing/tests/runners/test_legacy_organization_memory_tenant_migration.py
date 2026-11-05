"""The startup move of organization memory off the platform-wide `AIHub` owner onto the startup tenant."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.persistence.agents.agent_config_entity_document import AgentConfigEntityDocument

from swiss_ai_hub.api.runners.lifetime.legacy_organization_memory_tenant_migration import (
    LegacyOrganizationMemoryTenantMigration,
)

MIGRATION = LegacyOrganizationMemoryTenantMigration("default")


def _org_memory(tenant_id: str) -> dict:
    return {"tenant_id": tenant_id, "default_tenant_namespace": None, "allowed_tenant_namespaces": []}


def test_legacy_org_memory_scope_moves_to_the_startup_tenant():
    assert MIGRATION.rewritten({"org_memory": _org_memory("AIHub")}) == {"org_memory": _org_memory("default")}


def test_nested_scopes_are_found():
    config = {"capabilities": [{"memory": {"org_memory": _org_memory("AIHub")}}]}
    assert MIGRATION.rewritten(config) == {"capabilities": [{"memory": {"org_memory": _org_memory("default")}}]}


def test_a_real_tenant_is_left_alone():
    config = {"org_memory": _org_memory("tenant-b")}
    assert MIGRATION.rewritten(config) == config


def test_unrelated_tenant_ids_are_left_alone():
    """Mail and Teams configs carry an Entra `tenant_id` of their own."""
    config = {"imap": {"tenant_id": "AIHub", "client_id": "x"}}
    assert MIGRATION.rewritten(config) == config


@pytest.mark.asyncio
async def test_memories_are_adopted_by_the_startup_tenant():
    memory = MagicMock()
    memory.adopt_memories_of = AsyncMock(return_value=3)
    with patch(
        "swiss_ai_hub.api.runners.lifetime.legacy_organization_memory_tenant_migration.OrganizationMemory",
        return_value=memory,
    ) as organization_memory_class:
        adopted = await MIGRATION.adopt_memories(MagicMock())

    assert adopted == 3
    assert organization_memory_class.call_args.kwargs["tenant_id"] == "default"
    memory.adopt_memories_of.assert_awaited_once_with("AIHub")


async def _agent(agent_id: str, config_data: dict[str, Any]) -> AgentConfigEntityDocument:
    return await AgentConfigEntityDocument(
        agent_class="RAGAgent",
        agent_id=agent_id,
        name=LocaleString(en=agent_id),
        description=LocaleString(en=f"{agent_id} profile"),
        icon="meteor-icons:robot",
        config_data=config_data,
    ).insert()


@pytest.mark.beanie
class TestRetargetProfiles:
    async def test_stored_profiles_on_the_legacy_owner_are_rewritten_and_reported(self):
        legacy = await _agent("legacy", {"org_memory": _org_memory("AIHub")})
        await _agent("tenant", {"org_memory": _org_memory("tenant-b")})

        migrated = await MIGRATION.retarget_profiles()

        assert migrated == ["agent RAGAgent/legacy"]
        legacy = await AgentConfigEntityDocument.get(legacy.id)
        assert legacy.config_data == {"org_memory": _org_memory("default")}

    async def test_a_second_boot_rewrites_nothing(self):
        await _agent("legacy", {"org_memory": _org_memory("AIHub")})
        await MIGRATION.retarget_profiles()

        assert await MIGRATION.retarget_profiles() == []
