"""Mock fixtures for RoleEntity methods used in testing."""

from unittest.mock import patch

import pytest

from aihub_lib.persistence.access.entities.RoleEntity import RoleEntity


@pytest.fixture(autouse=True)
def mock_role_entity_methods():
    """
    Mock RoleEntity methods to ensure the 'TestOnlyFullAdminAccess' role is recognized during tests.

    This fixture addresses the issue where tests fail because the 'TestOnlyFullAdminAccess' role
    (used by DangerousDevelopmentOnlyAuthHandler) is not in the RoleEntity database.
    """
    original_filter_existing_roles = RoleEntity.filter_existing_roles
    original_get_access_rules_for_roles = RoleEntity.get_access_rules_for_roles

    def mock_filter_existing_roles(role_names, tenant_id=None):
        filtered_roles = original_filter_existing_roles(role_names, tenant_id)
        if "TestOnlyFullAdminAccess" in role_names and "TestOnlyFullAdminAccess" not in filtered_roles:
            filtered_roles.append("TestOnlyFullAdminAccess")
        return filtered_roles

    def mock_get_access_rules_for_roles(role_names, tenant_id=None):
        access_rules = original_get_access_rules_for_roles(role_names, tenant_id)
        if "TestOnlyFullAdminAccess" in role_names:
            access_rules.add("aihub.admin.>")
        return access_rules

    with patch.object(RoleEntity, "filter_existing_roles", side_effect=mock_filter_existing_roles):
        with patch.object(RoleEntity, "get_access_rules_for_roles", side_effect=mock_get_access_rules_for_roles):
            yield


@pytest.fixture(autouse=True)
def mock_role_entity_admin_only():
    """
    Mock RoleEntity methods for tests that only need admin access rules.
    Use this instead of the autouse fixture when you need more control.
    """
    original_get_access_rules_for_roles = RoleEntity.get_access_rules_for_roles

    def mock_get_access_rules_for_roles(role_names, tenant_id=None):
        access_rules = original_get_access_rules_for_roles(role_names, tenant_id)
        if "TestOnlyFullAdminAccess" in role_names:
            access_rules.add("aihub.admin.>")
        return access_rules

    with patch.object(RoleEntity, "get_access_rules_for_roles", side_effect=mock_get_access_rules_for_roles):
        yield
