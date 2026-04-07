from unittest.mock import MagicMock, patch

import pytest

from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.dependencies.dangerous_development_only_auth_handler.dangerous_development_only_auth_settings import (  # noqa: E501
    DangerousDevelopmentOnlyAuthSettings,
)
from swiss_ai_hub.core.persistence.access.entities.tenant_entity import TenantEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity

TEST_TENANT_ID = "__test_default_tenant__"
TEST_TENANT_NAME = "Test Default Tenant"
TEST_TENANT_ACCESS_RULES = ["aihub.admin.>"]


def _create_mock_tenant() -> MagicMock:
    """Create a mock TenantEntity that behaves like a default tenant.

    Does NOT use spec=TenantEntity because MongoEngine Document defines __len__,
    which makes MagicMock evaluate as falsy (len=0), breaking `if not tenant:` checks.
    """
    tenant = MagicMock()
    tenant.id = TEST_TENANT_ID
    tenant.name = TEST_TENANT_NAME
    tenant.access_rules = TEST_TENANT_ACCESS_RULES
    tenant.is_default = True
    return tenant


@pytest.fixture(autouse=True)
def mock_tenant_entity_autouse():
    """
    Mock TenantEntity, UserTenantRoleEntity, and AuthHandler tenant resolution for tests.

    This fixture ensures that auth handlers can resolve tenant context without a real database.
    It mocks:
    - TenantEntity.get_default_tenant() → returns a test tenant
    - TenantEntity.get_tenant_by_id() → returns the test tenant for any ID
    - UserTenantRoleEntity.get_roles_for_user_in_tenant() → returns dev roles
    - UserTenantRoleEntity.create_or_update() → no-op returning a mock
    - UserTenantRoleEntity.get_user_ids_in_tenant() → returns the dev user ID
    - AuthHandler._resolve_active_tenant() → returns the test tenant
    """
    config = DangerousDevelopmentOnlyAuthSettings()
    mock_tenant = _create_mock_tenant()

    def mock_get_roles(user_id, tenant_id):
        return config.ROLES

    def mock_create_or_update(user_id, tenant_id, roles, validate_roles=True):
        association = MagicMock()
        association.user_id = user_id
        association.tenant_id = tenant_id
        association.roles = roles
        return association

    def mock_get_user_ids_in_tenant(tenant_id):
        return [config.OID]

    def mock_resolve_active_tenant(user_id):
        return mock_tenant

    with (
        patch.object(TenantEntity, "get_default_tenant", return_value=mock_tenant),
        patch.object(TenantEntity, "get_tenant_by_id", return_value=mock_tenant),
        patch.object(TenantEntity, "get_tenant_by_name", return_value=mock_tenant),
        patch.object(TenantEntity, "ensure_default_tenant_exists", return_value=mock_tenant),
        patch.object(UserTenantRoleEntity, "get_roles_for_user_in_tenant", side_effect=mock_get_roles),
        patch.object(UserTenantRoleEntity, "create_or_update", side_effect=mock_create_or_update),
        patch.object(UserTenantRoleEntity, "get_user_ids_in_tenant", side_effect=mock_get_user_ids_in_tenant),
        patch.object(AuthHandler, "_resolve_active_tenant", side_effect=mock_resolve_active_tenant),
    ):
        yield
