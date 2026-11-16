from unittest.mock import AsyncMock, MagicMock

import pytest

from swiss_ai_hub.api.runners.lifetime.initialize_db import (
    _DEFAULT_ROLE_DEFINITIONS,
    _DefaultRoleDefinition,
    _reconcile_default_role_rules,
)

TENANT = "tenant-1"


def _role(access_rules: list[str]) -> MagicMock:
    return MagicMock(access_rules=list(access_rules), save_changes=AsyncMock())


class TestReconcileDefaultRoleRules:
    @pytest.mark.asyncio
    async def test_adds_rules_the_definition_gained_since_the_role_was_seeded(self):
        existing = _role(["aihub.admin.agent.>", "aihub.admin.knowledge.>"])
        definition = _DefaultRoleDefinition(
            name="AIHubKnowledgeAdmin",
            description="",
            access_rules=["aihub.admin.agent.>", "aihub.admin.knowledge", "aihub.admin.knowledge.>"],
        )

        await _reconcile_default_role_rules(existing, definition, TENANT)

        assert existing.access_rules == [
            "aihub.admin.agent.>",
            "aihub.admin.knowledge.>",
            "aihub.admin.knowledge",
        ]
        existing.save_changes.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_keeps_rules_an_admin_added_by_hand(self):
        existing = _role(["aihub.admin.knowledge.>", "aihub.admin.custom.thing"])
        definition = _DefaultRoleDefinition(
            name="AIHubKnowledgeAdmin", description="", access_rules=["aihub.admin.knowledge"]
        )

        await _reconcile_default_role_rules(existing, definition, TENANT)

        assert "aihub.admin.custom.thing" in existing.access_rules

    @pytest.mark.asyncio
    async def test_does_not_write_when_the_role_already_carries_every_rule(self):
        existing = _role(["aihub.admin.knowledge", "aihub.admin.knowledge.>"])
        definition = _DefaultRoleDefinition(
            name="AIHubKnowledgeAdmin",
            description="",
            access_rules=["aihub.admin.knowledge.>", "aihub.admin.knowledge"],
        )

        await _reconcile_default_role_rules(existing, definition, TENANT)

        existing.save_changes.assert_not_awaited()


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
