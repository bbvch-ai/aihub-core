"""The startup migration that gives knowledge admin roles seeded before the create-database guard its root rule."""

from unittest.mock import Mock, patch

import pytest
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity

from swiss_ai_hub.api.runners.lifetime.knowledge_root_rule_migration import KnowledgeRootRuleMigration

_SEEDED_BEFORE_ROOT = ["aihub.admin.agent.>", "aihub.admin.knowledge.>"]


def _role(tenant_id: str, *rules: str) -> Mock:
    role = Mock()
    role.name = "AIHubKnowledgeAdmin"
    role.tenant_id = tenant_id
    role.access_rules = list(rules)
    return role


def _run(*roles: Mock) -> list[str]:
    with patch.object(RoleEntity, "objects", return_value=list(roles)) as objects:
        migrated = KnowledgeRootRuleMigration.run()
    objects.assert_called_once_with(name="AIHubKnowledgeAdmin")
    return migrated


def test_adds_the_root_to_roles_still_as_seeded_in_every_tenant():
    startup = _role("default", *_SEEDED_BEFORE_ROOT)
    other = _role("admin", *reversed(_SEEDED_BEFORE_ROOT))

    migrated = _run(startup, other)

    assert startup.access_rules == [*_SEEDED_BEFORE_ROOT, "aihub.admin.knowledge"]
    assert other.access_rules == [*reversed(_SEEDED_BEFORE_ROOT), "aihub.admin.knowledge"]
    startup.save.assert_called_once()
    other.save.assert_called_once()
    assert migrated == ["role AIHubKnowledgeAdmin (default)", "role AIHubKnowledgeAdmin (admin)"]


def test_a_seeded_role_whose_root_was_removed_gets_it_back_until_the_migration_is_deleted():
    """Known limitation, kept visible on purpose: without the root, such a role is exactly the old seeded state.

    Removing the root from a role seeded before v0.321.0 cannot be told apart from never having had it, so the
    migration adds it again at every start. That is why it lives for one release only.
    """
    role = _role("default", *_SEEDED_BEFORE_ROOT, "aihub.admin.knowledge")
    role.access_rules.remove("aihub.admin.knowledge")

    _run(role)

    assert role.access_rules == [*_SEEDED_BEFORE_ROOT, "aihub.admin.knowledge"]


@pytest.mark.parametrize(
    "rules",
    [
        pytest.param(["aihub.admin.knowledge.>"], id="root-removed-on-purpose"),
        pytest.param([*_SEEDED_BEFORE_ROOT, "aihub.admin.service.>"], id="seeded-role-extended-by-an-admin"),
        pytest.param(
            ["aihub.admin.knowledge.handbook", "aihub.admin.knowledge.handbook.>"], id="narrowed-to-one-database"
        ),
        pytest.param([*_SEEDED_BEFORE_ROOT, "aihub.admin.knowledge"], id="already-has-the-root"),
    ],
)
def test_leaves_a_role_an_admin_has_edited_alone(rules: list[str]):
    """aihub-core-private#401: this runs on every start, so it must never put back a rule an admin removed."""
    role = _role("default", *rules)

    migrated = _run(role)

    assert role.access_rules == rules
    role.save.assert_not_called()
    assert migrated == []
