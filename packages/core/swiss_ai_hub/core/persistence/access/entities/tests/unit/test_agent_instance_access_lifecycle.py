"""Integration-style coverage of the per-instance access lifecycle (create grant → delete cleanup).

Exercises the real ``AccessChecker.from_user`` two-tier evaluation against FerretDB to prove that
the helpers used by ``AgentService`` actually flip a non-sysadmin creator's access on and off. The
orchestration that calls these helpers is unit-tested in ``packages/api``.
"""

import pytest

from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.auth.identity.tenant_identity import TenantIdentity
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity

TENANT_ID = "t1"
USER_ID = "u1"
AGENT_CLASS = "TestAgent"
AGENT_ID = "inst1"
ADMIN_RULE = f"aihub.admin.agent.{AGENT_CLASS}.{AGENT_ID}"
USER_RULE = f"aihub.user.agent.{AGENT_CLASS}.{AGENT_ID}"
ROLE_NAME = f"agent-{AGENT_CLASS}-{AGENT_ID}-admin"


pytestmark = pytest.mark.beanie


async def _current_user() -> UserIdentity:
    """Rebuilds the identity from the current DB state (tenant ceiling + held role names)."""
    tenant = await TenantMetadataEntity.get_metadata_by_tenant_id(TENANT_ID)
    roles = await UserTenantRoleEntity.get_roles_for_user_in_tenant(USER_ID, TENANT_ID)
    return UserIdentity(
        id=USER_ID,
        name="Creator",
        email="creator@test.local",
        roles=roles,
        acting_within_tenant=TenantIdentity(id=TENANT_ID, name="Tenant 1", access_rules=tenant.access_rules),
        is_sys_admin=False,
    )


async def _grant_instance_access() -> None:
    """Mirrors AgentService._grant_instance_access using the real helpers."""
    tenant = await TenantMetadataEntity.get_metadata_by_tenant_id(TENANT_ID)
    if not AccessChecker.rules_grant_admin_to_agent_instance(tenant.access_rules, AGENT_CLASS, AGENT_ID):
        await TenantMetadataEntity.grant_access_rule(TENANT_ID, ADMIN_RULE)
    if not await RoleEntity.get_role(ROLE_NAME, TENANT_ID):
        await RoleEntity.create_tenant_role(ROLE_NAME, "Admin access", [ADMIN_RULE], TENANT_ID)
    await UserTenantRoleEntity.add_roles(USER_ID, TENANT_ID, [ROLE_NAME], validate_roles=False)


async def _cleanup_instance_access() -> None:
    """Mirrors delete_agent_instance cleanup using the real helpers."""
    await TenantMetadataEntity.revoke_access_rule_from_all_tenants([USER_RULE, ADMIN_RULE])
    await RoleEntity.delete_role_from_all_tenants(ROLE_NAME)


async def test_tenant_ceiling_is_the_blocker_and_grant_unblocks() -> None:
    """User role is broad; the class-level tenant ceiling blocks the instance until granted."""
    await TenantMetadataEntity.create_tenant_metadata(
        TENANT_ID, "Tenant 1", access_rules=[f"aihub.admin.agent.{AGENT_CLASS}"]
    )
    await RoleEntity.create_tenant_role("BroadAgentAdmin", "desc", ["aihub.admin.agent.>"], TENANT_ID)
    await UserTenantRoleEntity.create_or_update(USER_ID, TENANT_ID, ["BroadAgentAdmin"], validate_roles=False)

    assert not (await AccessChecker.from_user(await _current_user())).has_access_to_agent(AGENT_CLASS, AGENT_ID)

    await _grant_instance_access()
    assert (await AccessChecker.from_user(await _current_user())).has_access_to_agent(AGENT_CLASS, AGENT_ID)

    await _cleanup_instance_access()
    assert not (await AccessChecker.from_user(await _current_user())).has_access_to_agent(AGENT_CLASS, AGENT_ID)


async def test_user_role_is_the_blocker_and_per_instance_role_unblocks() -> None:
    """Tenant ceiling is broad; the narrow user role blocks the instance until the per-instance role is assigned."""
    await TenantMetadataEntity.create_tenant_metadata(TENANT_ID, "Tenant 1", access_rules=["aihub.admin.>"])
    await RoleEntity.create_tenant_role("NarrowAdmin", "desc", [f"aihub.admin.agent.{AGENT_CLASS}"], TENANT_ID)
    await UserTenantRoleEntity.create_or_update(USER_ID, TENANT_ID, ["NarrowAdmin"], validate_roles=False)

    assert not (await AccessChecker.from_user(await _current_user())).has_access_to_agent(AGENT_CLASS, AGENT_ID)

    await _grant_instance_access()
    assert (await AccessChecker.from_user(await _current_user())).has_access_to_agent(AGENT_CLASS, AGENT_ID)

    await _cleanup_instance_access()
    assert not (await AccessChecker.from_user(await _current_user())).has_access_to_agent(AGENT_CLASS, AGENT_ID)


async def test_grant_is_idempotent_on_recreate() -> None:
    """Re-running the grant (e.g. create logic runs again) adds no duplicate rule or role."""
    await TenantMetadataEntity.create_tenant_metadata(
        TENANT_ID, "Tenant 1", access_rules=[f"aihub.admin.agent.{AGENT_CLASS}"]
    )
    await RoleEntity.create_tenant_role("BroadAgentAdmin", "desc", ["aihub.admin.agent.>"], TENANT_ID)
    await UserTenantRoleEntity.create_or_update(USER_ID, TENANT_ID, ["BroadAgentAdmin"], validate_roles=False)

    await _grant_instance_access()
    await _grant_instance_access()

    tenant = await TenantMetadataEntity.get_metadata_by_tenant_id(TENANT_ID)
    assert tenant.access_rules.count(ADMIN_RULE) == 1
    assert await RoleEntity.find({"name": ROLE_NAME, "tenant_id": TENANT_ID}).count() == 1
    assert (await UserTenantRoleEntity.get_roles_for_user_in_tenant(USER_ID, TENANT_ID)).count(ROLE_NAME) == 1
