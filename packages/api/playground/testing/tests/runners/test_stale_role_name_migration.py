"""The startup removal of role names that a deletion before the cascade fix left on users."""

from unittest.mock import Mock, patch

from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity

from swiss_ai_hub.api.runners.lifetime.stale_role_name_migration import StaleRoleNameMigration


def _role(tenant_id: str, name: str) -> Mock:
    role = Mock()
    role.tenant_id = tenant_id
    role.name = name
    return role


def _assignment(user_id: str, tenant_id: str, *roles: str) -> Mock:
    assignment = Mock()
    assignment.user_id = user_id
    assignment.tenant_id = tenant_id
    assignment.roles = list(roles)
    return assignment


def _run(roles: list[Mock], assignments: list[Mock]) -> list[str]:
    with (
        patch.object(RoleEntity, "objects", return_value=roles),
        patch.object(UserTenantRoleEntity, "objects", return_value=assignments),
    ):
        return StaleRoleNameMigration.run()


def test_a_name_without_a_role_is_removed_and_reported():
    assignment = _assignment("user-1", "tenant-1", "AIHubUser", "Sales")

    migrated = _run([_role("tenant-1", "AIHubUser")], [assignment])

    assert assignment.roles == ["AIHubUser"]
    assignment.save.assert_called_once()
    assert migrated == ["user user-1 in tenant tenant-1 (Sales)"]


def test_a_role_of_the_same_name_in_another_tenant_does_not_keep_the_name():
    """Roles are tenant-scoped, so another tenant's `Sales` must not keep this tenant's stale `Sales`."""
    assignment = _assignment("user-1", "tenant-1", "Sales")

    _run([_role("tenant-2", "Sales")], [assignment])

    assert assignment.roles == []
    assignment.save.assert_called_once()


def test_an_assignment_whose_roles_all_exist_is_left_untouched():
    assignment = _assignment("user-1", "tenant-1", "AIHubUser", "AIHubAdmin")

    migrated = _run([_role("tenant-1", "AIHubUser"), _role("tenant-1", "AIHubAdmin")], [assignment])

    assert assignment.roles == ["AIHubUser", "AIHubAdmin"]
    assignment.save.assert_not_called()
    assert migrated == []
