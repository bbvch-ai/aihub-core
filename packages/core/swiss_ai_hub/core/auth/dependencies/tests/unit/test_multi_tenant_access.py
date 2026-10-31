"""Multi-tenant access control: a user's roles differ per tenant, and each tenant's rules cap them."""

import pytest
import pytest_asyncio

from swiss_ai_hub.core.auth.access.access_checker import AccessChecker, AccessLevel
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity

pytestmark = pytest.mark.beanie

ALPHA = "alpha-corp"
BETA = "beta-inc"
AGENT = "aihub.user.agent.class-a.id-1"
PROCESS = "aihub.user.process.class-a.id-1"


@pytest_asyncio.fixture(loop_scope="session", autouse=True)
async def tenants_with_default_roles(clean_beanie_collections: None) -> None:
    await TenantMetadataEntity.create_tenant_metadata(ALPHA, "Alpha Corp", "Tenant Alpha Corp", ["aihub.admin.>"])
    await TenantMetadataEntity.create_tenant_metadata(BETA, "Beta Inc", "Tenant Beta Inc", ["aihub.user.agent.>"])
    for tenant_id in (ALPHA, BETA):
        await RoleEntity.create_tenant_role("AIHubAdmin", "Role AIHubAdmin", ["aihub.admin.>"], tenant_id)
        await RoleEntity.create_tenant_role("AIHubUser", "Role AIHubUser", ["aihub.user.>"], tenant_id)


async def access_level(user_id: str, tenant_id: str, permission_template: str) -> AccessLevel:
    tenant = await TenantMetadataEntity.get_metadata_by_tenant_id(tenant_id)
    user_roles = await UserTenantRoleEntity.get_roles_for_user_in_tenant(user_id, tenant_id)
    user_access_rules = await RoleEntity.get_access_rules_for_roles(user_roles, tenant_id)
    checker = AccessChecker(list(user_access_rules), tenant_access_rules=tenant.access_rules)
    return checker.access_level(permission_template)


async def test_user_with_admin_in_one_tenant_and_user_in_another_gets_correct_access_levels() -> None:
    await UserTenantRoleEntity.create_or_update("multi-tenant-user", ALPHA, ["AIHubAdmin"])
    await UserTenantRoleEntity.create_or_update("multi-tenant-user", BETA, ["AIHubUser"])

    assert await access_level("multi-tenant-user", ALPHA, AGENT) is AccessLevel.ACCESS_ADMIN
    assert await access_level("multi-tenant-user", BETA, AGENT) is AccessLevel.ACCESS_USER


async def test_tenant_access_rules_cap_user_permissions() -> None:
    await UserTenantRoleEntity.create_or_update("capped-user", BETA, ["AIHubAdmin"])

    assert await access_level("capped-user", BETA, AGENT) is AccessLevel.ACCESS_USER
    assert await access_level("capped-user", BETA, PROCESS) is AccessLevel.ACCESS_DENIED


async def test_user_gets_denied_for_resource_outside_tenants_access_rules() -> None:
    await UserTenantRoleEntity.create_or_update("limited-user", BETA, ["AIHubUser"])

    assert await access_level("limited-user", BETA, PROCESS) is AccessLevel.ACCESS_DENIED


async def test_same_user_has_different_implicit_access_across_tenants() -> None:
    await UserTenantRoleEntity.create_or_update("implicit-user", ALPHA, ["AIHubUser"])
    await UserTenantRoleEntity.create_or_update("implicit-user", BETA, ["AIHubUser"])

    assert await access_level("implicit-user", ALPHA, "aihub.user.process.?>") is AccessLevel.ACCESS_USER
    assert await access_level("implicit-user", BETA, "aihub.user.process.?>") is AccessLevel.ACCESS_DENIED
