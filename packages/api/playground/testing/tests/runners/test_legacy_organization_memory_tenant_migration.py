"""The startup move of organization memory off the platform-wide `AIHub` owner onto the startup tenant."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

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
