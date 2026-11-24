"""The startup migration that gives knowledge admin roles seeded before the create-database guard its root rule."""

from unittest.mock import Mock, patch

from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity

from swiss_ai_hub.api.runners.lifetime.knowledge_root_rule_migration import KnowledgeRootRuleMigration


def _role(tenant_id: str, *rules: str) -> Mock:
    role = Mock()
    role.name = "AIHubKnowledgeAdmin"
    role.tenant_id = tenant_id
    role.access_rules = list(rules)
    return role


def test_adds_the_root_next_to_the_wildcard_in_every_tenant():
    startup = _role("default", "aihub.admin.knowledge.>")
    other = _role("admin", "aihub.admin.agent.>", "aihub.admin.knowledge.>")

    with patch.object(RoleEntity, "objects", return_value=[startup, other]):
        migrated = KnowledgeRootRuleMigration.run()

    assert startup.access_rules == ["aihub.admin.knowledge.>", "aihub.admin.knowledge"]
    assert other.access_rules == ["aihub.admin.agent.>", "aihub.admin.knowledge.>", "aihub.admin.knowledge"]
    startup.save.assert_called_once()
    other.save.assert_called_once()
    assert migrated == ["role AIHubKnowledgeAdmin (default)", "role AIHubKnowledgeAdmin (admin)"]


def test_queries_only_the_default_role_that_still_holds_the_wildcard():
    """A custom role never could create a database, and a role narrowed to named databases was narrowed on purpose."""
    with patch.object(RoleEntity, "objects", return_value=[]) as objects:
        KnowledgeRootRuleMigration.run()

    objects.assert_called_once_with(name="AIHubKnowledgeAdmin", access_rules="aihub.admin.knowledge.>")


def test_leaves_a_role_that_already_has_the_root_alone():
    role = _role("default", "aihub.admin.knowledge", "aihub.admin.knowledge.>")

    with patch.object(RoleEntity, "objects", return_value=[role]):
        migrated = KnowledgeRootRuleMigration.run()

    role.save.assert_not_called()
    assert migrated == []
