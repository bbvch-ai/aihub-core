"""Seeding the default roles, which runs on every API start and on every tenant provisioning push."""

from collections.abc import Iterator
from contextlib import contextmanager
from unittest.mock import MagicMock, Mock, patch

import pytest
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity

from swiss_ai_hub.api.runners.lifetime.initialize_db import (
    _DEFAULT_ROLE_DEFINITIONS,
    initialize_default_roles_for_tenant,
)

TENANT = "tenant-1"
_MODULE = "swiss_ai_hub.api.runners.lifetime.initialize_db"


def _role(access_rules: list[str]) -> MagicMock:
    return MagicMock(access_rules=list(access_rules))


def _all_default_roles_stored() -> dict[str, MagicMock]:
    return {definition.name: _role(definition.access_rules) for definition in _DEFAULT_ROLE_DEFINITIONS}


@contextmanager
def _stored(roles: dict[str, MagicMock], *, create_default_roles: bool = True) -> Iterator[Mock]:
    """Serves ``roles`` by name as the tenant's stored roles and yields the patched ``create_tenant_role``."""

    def objects(name: str, tenant_id: str) -> Mock:
        assert tenant_id == TENANT
        return Mock(first=Mock(return_value=roles.get(name)))

    with (
        patch(f"{_MODULE}.AIHubSettings", return_value=Mock(CREATE_DEFAULT_ROLES=create_default_roles)),
        patch.object(RoleEntity, "objects", side_effect=objects),
        patch.object(RoleEntity, "create_tenant_role") as create_tenant_role,
    ):
        yield create_tenant_role


class TestInitializeDefaultRolesForTenant:
    @pytest.mark.asyncio
    async def test_a_narrowed_user_role_keeps_its_rules(self):
        """aihub-core-private#401: a restart put `aihub.user.>` back on an `AIHubUser` an admin had narrowed."""
        roles = _all_default_roles_stored()
        narrowed = ["aihub.user.service.>", "aihub.user.agent.RAGAgent.hr-assistant"]
        roles["AIHubUser"] = _role(narrowed)

        with _stored(roles) as create_tenant_role:
            await initialize_default_roles_for_tenant(TENANT)

        assert roles["AIHubUser"].access_rules == narrowed
        roles["AIHubUser"].save.assert_not_called()
        create_tenant_role.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_stored_default_role_is_written(self):
        """Seeding never edits a stored role, not even one missing a rule its definition has."""
        roles = _all_default_roles_stored()
        roles["AIHubKnowledgeAdmin"] = _role(["aihub.admin.knowledge.>"])

        with _stored(roles):
            await initialize_default_roles_for_tenant(TENANT)

        assert roles["AIHubKnowledgeAdmin"].access_rules == ["aihub.admin.knowledge.>"]
        for role in roles.values():
            role.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_a_missing_default_role_is_created_with_its_definition(self):
        roles = _all_default_roles_stored()
        del roles["AIHubKnowledgeUser"]

        with _stored(roles) as create_tenant_role:
            await initialize_default_roles_for_tenant(TENANT)

        create_tenant_role.assert_called_once_with(
            name="AIHubKnowledgeUser",
            description="Grants access to all knowledge databases but to nothing else",
            access_rules=["aihub.user.knowledge.>"],
            tenant_id=TENANT,
        )

    @pytest.mark.asyncio
    async def test_nothing_is_created_when_default_roles_are_turned_off(self):
        with _stored({}, create_default_roles=False) as create_tenant_role:
            await initialize_default_roles_for_tenant(TENANT)

        create_tenant_role.assert_not_called()


class TestKnowledgeAdminDefinition:
    def test_carries_both_the_root_and_the_wildcard_knowledge_rule(self):
        """The bare root guards create-database; the wildcard covers databases that exist."""
        definition = next(d for d in _DEFAULT_ROLE_DEFINITIONS if d.name == "AIHubKnowledgeAdmin")

        assert "aihub.admin.knowledge" in definition.access_rules
        assert "aihub.admin.knowledge.>" in definition.access_rules

    def test_is_scoped_to_knowledge_like_the_other_scoped_roles(self):
        """Admin over every agent used to ride along; a knowledge admin is a knowledge admin only."""
        definition = next(d for d in _DEFAULT_ROLE_DEFINITIONS if d.name == "AIHubKnowledgeAdmin")

        assert all(rule.startswith("aihub.admin.knowledge") for rule in definition.access_rules)

    def test_has_a_user_counterpart_like_agents_and_processes(self):
        definition = next(d for d in _DEFAULT_ROLE_DEFINITIONS if d.name == "AIHubKnowledgeUser")

        assert definition.access_rules == ["aihub.user.knowledge.>"]
