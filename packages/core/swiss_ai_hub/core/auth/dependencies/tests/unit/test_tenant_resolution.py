"""Tenant resolution in the auth handler: users are scoped to the tenant they name or have made active."""

from collections.abc import Generator
from typing import Any
from unittest.mock import patch

import pytest
import pytest_asyncio
from fastapi import HTTPException, Request

from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.identity.tenant_identity import TenantIdentity
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity

pytestmark = pytest.mark.beanie

DEFAULT_TENANT = "default"
SECOND_TENANT = "acme-corp"
UNKNOWN_OBJECT_ID = "000000000000000000000000"
NO_ACTIVE_TENANT = "No active tenant set"
STALE_ACTIVE_TENANT = "Your active tenant is no longer accessible"
ACCESS_DENIED = "Access denied"


class ConcreteAuthHandler(AuthHandler):
    """Concrete implementation of AuthHandler for testing tenant resolution methods."""

    async def __call__(self, request: Request) -> UserIdentity:
        raise NotImplementedError("Not used in tenant resolution tests")

    async def authenticate_token(self, token: str) -> UserIdentity:
        raise NotImplementedError("Not used in tenant resolution tests")


@pytest.fixture
def active_tenants() -> Generator[dict[str, str | None]]:
    """Mock KeycloakAdminService active-tenant + membership methods with in-memory stores.

    Membership is derived from ``UserTenantRoleEntity`` rows: if a user has a role row in a tenant, they are
    treated as a Keycloak member of that tenant, without requiring tests to also create Keycloak group memberships.
    """
    active: dict[str, str | None] = {}

    async def mock_get_active_tenant_id(user_id: str) -> str | None:  # noqa: S7503
        return active.get(user_id)

    async def mock_set_active_tenant(user_id: str, tenant_id: str) -> None:  # noqa: S7503
        active[user_id] = tenant_id

    async def mock_clear_active_tenant(user_id: str) -> None:  # noqa: S7503
        active.pop(user_id, None)

    async def mock_tenant_exists(tenant_id: str) -> bool:
        return await TenantMetadataEntity.get_metadata_by_tenant_id(tenant_id) is not None

    async def mock_get_user_tenant_ids(user_id: str) -> set[str]:
        return set(await UserTenantRoleEntity.get_tenant_ids_for_user(user_id))

    async def mock_is_user_member_of_tenant(user_id: str, tenant_id: str) -> bool:
        return bool(await UserTenantRoleEntity.get_roles_for_user_in_tenant(user_id, tenant_id))

    with (
        patch.object(KeycloakAdminService, "get_active_tenant_id", side_effect=mock_get_active_tenant_id),
        patch.object(KeycloakAdminService, "set_active_tenant", side_effect=mock_set_active_tenant),
        patch.object(KeycloakAdminService, "clear_active_tenant", side_effect=mock_clear_active_tenant),
        patch.object(KeycloakAdminService, "tenant_exists", side_effect=mock_tenant_exists),
        patch.object(KeycloakAdminService, "get_user_tenant_ids", side_effect=mock_get_user_tenant_ids),
        patch.object(KeycloakAdminService, "is_user_member_of_tenant", side_effect=mock_is_user_member_of_tenant),
    ):
        yield active


@pytest_asyncio.fixture(loop_scope="session", autouse=True)
async def tenants_and_memberships(clean_beanie_collections: None) -> None:
    await TenantMetadataEntity.create_tenant_metadata(
        DEFAULT_TENANT, "Default Org", "Default tenant for testing", ["aihub.admin.>"]
    )
    await TenantMetadataEntity.create_tenant_metadata(
        SECOND_TENANT, "Acme Corp", "Second tenant for testing", ["aihub.user.>"]
    )
    for tenant_id in (DEFAULT_TENANT, SECOND_TENANT):
        await RoleEntity.create_tenant_role("AIHubUser", "Role AIHubUser for testing", ["aihub.user.>"], tenant_id)
    await UserTenantRoleEntity.create_or_update("user-1", DEFAULT_TENANT, ["AIHubUser"])
    await UserTenantRoleEntity.create_or_update("user-1", SECOND_TENANT, ["AIHubUser"])
    await UserTenantRoleEntity.create_or_update("user-2", DEFAULT_TENANT, ["AIHubUser"])


def request_for(tenant_id: str) -> Request:
    scope: dict[str, Any] = {
        "type": "http",
        "headers": [],
        "method": "GET",
        "path": "/",
        "path_params": {"tenant_id": tenant_id},
    }
    return Request(scope)


async def resolve(user_id: str, tenant_id: str) -> TenantIdentity:
    return await ConcreteAuthHandler().resolve_tenant_for_user(request_for(tenant_id), user_id)


async def resolution_error(user_id: str, tenant_id: str) -> HTTPException:
    with pytest.raises(HTTPException) as excinfo:
        await resolve(user_id, tenant_id)
    return excinfo.value


async def active_tenant_error(user_id: str) -> HTTPException:
    with pytest.raises(HTTPException) as excinfo:
        await ConcreteAuthHandler().get_active_tenant_for_user(user_id)
    return excinfo.value


def assert_error(error: HTTPException, status_code: int, message: str) -> None:
    assert error.status_code == status_code
    assert message in error.detail


async def test_explicit_tenant_path_parameter_resolves_to_specified_tenant(active_tenants: dict) -> None:
    assert (await resolve("user-1", SECOND_TENANT)).name == "Acme Corp"


async def test_active_tenant_path_parameter_without_active_tenant_returns_400(active_tenants: dict) -> None:
    assert_error(await resolution_error("user-1", "active"), 400, NO_ACTIVE_TENANT)


async def test_invalid_tenant_id_returns_403(active_tenants: dict) -> None:
    assert_error(await resolution_error("user-1", "non-existent-tenant-id"), 403, ACCESS_DENIED)


async def test_user_without_tenant_membership_returns_403(active_tenants: dict) -> None:
    assert_error(await resolution_error("user-2", SECOND_TENANT), 403, ACCESS_DENIED)


async def test_no_active_tenant_set_returns_400_regardless_of_default_tenant(active_tenants: dict) -> None:
    await TenantMetadataEntity.delete_tenant_metadata(DEFAULT_TENANT)

    assert_error(await resolution_error("user-1", "active"), 400, NO_ACTIVE_TENANT)


async def test_get_active_tenant_for_user_without_active_tenant_returns_400(active_tenants: dict) -> None:
    assert_error(await active_tenant_error("user-1"), 400, NO_ACTIVE_TENANT)


async def test_get_active_tenant_for_user_with_active_tenant_set_resolves_correctly(active_tenants: dict) -> None:
    active_tenants["user-1"] = SECOND_TENANT

    assert (await ConcreteAuthHandler().get_active_tenant_for_user("user-1")).name == "Acme Corp"


async def test_non_existent_tenant_id_returns_generic_403_without_leaking_information(active_tenants: dict) -> None:
    assert_error(await resolution_error("user-1", UNKNOWN_OBJECT_ID), 403, ACCESS_DENIED)


async def test_superuser_virtual_tenant_id_cannot_be_used_by_regular_users(active_tenants: dict) -> None:
    assert_error(await resolution_error("user-1", "__superuser_tenant__"), 403, ACCESS_DENIED)


async def test_active_tenant_is_used_when_path_parameter_is_active(active_tenants: dict) -> None:
    active_tenants["user-1"] = SECOND_TENANT

    assert (await resolve("user-1", "active")).name == "Acme Corp"


async def test_explicit_tenant_path_parameter_does_not_update_active_tenant(active_tenants: dict) -> None:
    active_tenants["user-1"] = DEFAULT_TENANT

    assert (await resolve("user-1", SECOND_TENANT)).name == "Acme Corp"
    assert active_tenants["user-1"] == DEFAULT_TENANT


async def test_stale_active_tenant_returns_400(active_tenants: dict) -> None:
    active_tenants["user-1"] = UNKNOWN_OBJECT_ID

    assert_error(await resolution_error("user-1", "active"), 400, STALE_ACTIVE_TENANT)


async def test_active_tenant_without_membership_returns_400(active_tenants: dict) -> None:
    active_tenants["user-2"] = SECOND_TENANT

    assert_error(await resolution_error("user-2", "active"), 400, STALE_ACTIVE_TENANT)


async def test_websocket_context_uses_active_tenant(active_tenants: dict) -> None:
    active_tenants["user-1"] = SECOND_TENANT

    assert (await ConcreteAuthHandler().get_active_tenant_for_user("user-1")).name == "Acme Corp"


async def test_websocket_with_stale_active_tenant_returns_400(active_tenants: dict) -> None:
    active_tenants["user-1"] = UNKNOWN_OBJECT_ID

    assert_error(await active_tenant_error("user-1"), 400, STALE_ACTIVE_TENANT)


async def test_websocket_with_revoked_tenant_membership_returns_400(active_tenants: dict) -> None:
    active_tenants["user-2"] = SECOND_TENANT

    assert_error(await active_tenant_error("user-2"), 400, STALE_ACTIVE_TENANT)
