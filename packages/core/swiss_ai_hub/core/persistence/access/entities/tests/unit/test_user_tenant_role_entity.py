"""User-tenant-role management: assigning and managing a user's roles within a tenant."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity

pytestmark = pytest.mark.beanie

TENANT_ID = "default"


@pytest.fixture(autouse=True)
def mock_keycloak_active_tenant() -> Generator[None]:
    """Mock KeycloakAdminService active tenant methods for tests."""
    with (
        patch.object(KeycloakAdminService, "get_active_tenant_id", new_callable=AsyncMock, return_value=None),
        patch.object(KeycloakAdminService, "set_active_tenant", new_callable=AsyncMock),
        patch.object(KeycloakAdminService, "clear_active_tenant", new_callable=AsyncMock),
    ):
        yield


@pytest_asyncio.fixture(loop_scope="session", autouse=True)
async def default_tenant_with_roles(clean_beanie_collections: None) -> None:
    await TenantMetadataEntity.ensure_startup_tenant_metadata_exists(
        tenant_id=TENANT_ID,
        name="Test Default Tenant",
        description="Default tenant for testing",
        access_rules=["aihub.admin.>"],
    )
    await RoleEntity.create_tenant_role("AIHubUser", "Role AIHubUser for testing", ["aihub.user.>"], TENANT_ID)
    await RoleEntity.create_tenant_role("AIHubAdmin", "Role AIHubAdmin for testing", ["aihub.admin.>"], TENANT_ID)


async def roles_of(user_id: str) -> set[str]:
    return set(await UserTenantRoleEntity.get_roles_for_user_in_tenant(user_id, TENANT_ID))


async def test_create_a_new_user_tenant_role_association() -> None:
    await UserTenantRoleEntity.create_or_update("user-123", TENANT_ID, ["AIHubUser"])

    assert await roles_of("user-123") == {"AIHubUser"}


async def test_update_an_existing_user_tenant_role_association() -> None:
    await UserTenantRoleEntity.create_or_update("user-456", TENANT_ID, ["AIHubUser"])

    await UserTenantRoleEntity.create_or_update("user-456", TENANT_ID, ["AIHubAdmin"])

    assert await roles_of("user-456") == {"AIHubAdmin"}


async def test_add_roles_to_an_existing_association() -> None:
    await UserTenantRoleEntity.create_or_update("user-789", TENANT_ID, ["AIHubUser"])

    await UserTenantRoleEntity.add_roles("user-789", TENANT_ID, ["AIHubAdmin"])

    assert await roles_of("user-789") == {"AIHubUser", "AIHubAdmin"}


async def test_remove_roles_from_an_existing_association() -> None:
    await UserTenantRoleEntity.create_or_update("user-remove", TENANT_ID, ["AIHubUser", "AIHubAdmin"])

    await UserTenantRoleEntity.remove_roles("user-remove", TENANT_ID, ["AIHubAdmin"])

    assert await roles_of("user-remove") == {"AIHubUser"}


async def test_remove_user_from_tenant() -> None:
    await UserTenantRoleEntity.create_or_update("user-delete", TENANT_ID, ["AIHubUser"])

    assert await UserTenantRoleEntity.remove_user_from_tenant("user-delete", TENANT_ID)

    assert await UserTenantRoleEntity.get_by_user_and_tenant("user-delete", TENANT_ID) is None


async def test_get_roles_for_user_with_no_association() -> None:
    assert await UserTenantRoleEntity.get_roles_for_user_in_tenant("user-no-assoc", TENANT_ID) == []


async def test_creating_association_with_invalid_roles_ignores_them() -> None:
    await UserTenantRoleEntity.create_or_update("user-invalid", TENANT_ID, ["AIHubUser", "NonExistentRole"])

    assert await roles_of("user-invalid") == {"AIHubUser"}


async def test_adding_invalid_roles_ignores_them() -> None:
    await UserTenantRoleEntity.create_or_update("user-add-invalid", TENANT_ID, ["AIHubUser"])

    await UserTenantRoleEntity.add_roles("user-add-invalid", TENANT_ID, ["NonExistentRole"])

    assert await roles_of("user-add-invalid") == {"AIHubUser"}


async def test_create_association_with_validation_disabled_accepts_any_roles() -> None:
    await UserTenantRoleEntity.create_or_update("user-no-validate", TENANT_ID, ["FakeRole"], validate_roles=False)

    assert await roles_of("user-no-validate") == {"FakeRole"}
