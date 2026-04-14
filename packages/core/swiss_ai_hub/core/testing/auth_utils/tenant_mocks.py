from unittest.mock import MagicMock, patch

import pytest

from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.dependencies.dangerous_development_only_auth_handler.dangerous_development_only_auth_settings import (  # noqa: E501
    DangerousDevelopmentOnlyAuthSettings,
)
from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity

TEST_TENANT_ID = "__test_default_tenant__"
TEST_TENANT_NAME = "Test Default Tenant"
TEST_TENANT_ACCESS_RULES = ["aihub.admin.>"]


def _create_mock_tenant() -> MagicMock:
    """Create a mock TenantMetadataEntity that behaves like a default tenant.

    Does NOT use spec=TenantMetadataEntity because MongoEngine Document defines __len__,
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
    Mock tenant metadata, membership roles, Keycloak existence, and auth tenant resolution for tests.

    This fixture ensures that auth handlers can resolve tenant context without a real database
    or Keycloak. It mocks:
    - TenantMetadataEntity.get_default_tenant_metadata() → returns test metadata
    - TenantMetadataEntity.get_metadata_by_tenant_id() → returns the test metadata for any id
    - TenantMetadataEntity.ensure_default_tenant_metadata_exists() → returns the test metadata
    - KeycloakAdminService.tenant_exists() → True (tests act as if Keycloak acknowledges the tenant)
    - KeycloakAdminService.filter_existing_tenant_ids() → echoes the input (all exist)
    - UserTenantRoleEntity.get_roles_for_user_in_tenant() → returns dev roles
    - UserTenantRoleEntity.create_or_update() → no-op returning a mock
    - UserTenantRoleEntity.get_user_ids_in_tenant() → returns the dev user ID
    - AuthHandler._resolve_active_tenant() → returns the test metadata
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

    async def mock_resolve_active_tenant(user_id):
        return mock_tenant

    async def mock_tenant_exists(tenant_id):
        return True

    async def mock_filter_existing_tenant_ids(tenant_ids):
        return set(tenant_ids)

    with (
        patch.object(TenantMetadataEntity, "get_default_tenant_metadata", return_value=mock_tenant),
        patch.object(TenantMetadataEntity, "get_metadata_by_tenant_id", return_value=mock_tenant),
        patch.object(TenantMetadataEntity, "ensure_default_tenant_metadata_exists", return_value=mock_tenant),
        patch.object(KeycloakAdminService, "tenant_exists", side_effect=mock_tenant_exists),
        patch.object(KeycloakAdminService, "filter_existing_tenant_ids", side_effect=mock_filter_existing_tenant_ids),
        patch.object(UserTenantRoleEntity, "get_roles_for_user_in_tenant", side_effect=mock_get_roles),
        patch.object(UserTenantRoleEntity, "create_or_update", side_effect=mock_create_or_update),
        patch.object(UserTenantRoleEntity, "get_user_ids_in_tenant", side_effect=mock_get_user_ids_in_tenant),
        patch.object(AuthHandler, "_resolve_active_tenant", side_effect=mock_resolve_active_tenant),
    ):
        yield
