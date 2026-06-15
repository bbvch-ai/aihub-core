"""Integration-style coverage of the per-instance access lifecycle (create grant → delete cleanup).

Exercises the real ``AccessChecker.from_user`` two-tier evaluation against FerretDB to prove that
the helpers used by ``AgentService`` actually flip a non-sysadmin creator's access on and off. The
orchestration that calls these helpers is unit-tested in ``packages/api``.
"""

from collections.abc import Generator

import pytest
from mongoengine import connect, disconnect

from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.auth.identity.tenant_identity import TenantIdentity
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
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


@pytest.fixture
def mongo_connection() -> Generator[None]:
    connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
    )
    yield
    disconnect()


@pytest.fixture(autouse=True)
def clean_collections(mongo_connection: None) -> Generator[None]:
    for entity in (TenantMetadataEntity, RoleEntity, UserTenantRoleEntity):
        entity.objects.delete()
    yield
    for entity in (TenantMetadataEntity, RoleEntity, UserTenantRoleEntity):
        entity.objects.delete()


def _current_user() -> UserIdentity:
    """Rebuilds the identity from the current DB state (tenant ceiling + held role names)."""
    tenant = TenantMetadataEntity.get_metadata_by_tenant_id(TENANT_ID)
    roles = UserTenantRoleEntity.get_roles_for_user_in_tenant(USER_ID, TENANT_ID)
    return UserIdentity(
        id=USER_ID,
        name="Creator",
        email="creator@test.local",
        roles=roles,
        acting_within_tenant=TenantIdentity(id=TENANT_ID, name="Tenant 1", access_rules=tenant.access_rules),
        is_sys_admin=False,
    )


def _grant_creator_access() -> None:
    """Mirrors AgentService._grant_creator_access using the real helpers."""
    tenant = TenantMetadataEntity.get_metadata_by_tenant_id(TENANT_ID)
    if not AccessChecker.rules_grant_admin_to_agent(tenant.access_rules, AGENT_CLASS, AGENT_ID):
        TenantMetadataEntity.grant_access_rule(TENANT_ID, ADMIN_RULE)
    if not RoleEntity.objects(name=ROLE_NAME, tenant_id=TENANT_ID).first():
        RoleEntity.create_tenant_role(ROLE_NAME, "Admin access", [ADMIN_RULE], TENANT_ID)
    UserTenantRoleEntity.add_roles(USER_ID, TENANT_ID, [ROLE_NAME], validate_roles=False)


def _cleanup_instance_access() -> None:
    """Mirrors delete_agent_instance cleanup using the real helpers."""
    TenantMetadataEntity.revoke_access_rule_from_all_tenants([USER_RULE, ADMIN_RULE])
    RoleEntity.delete_role_from_all_tenants(ROLE_NAME)


def test_tenant_ceiling_is_the_blocker_and_grant_unblocks() -> None:
    """User role is broad; the class-level tenant ceiling blocks the instance until granted."""
    TenantMetadataEntity.create_tenant_metadata(
        TENANT_ID, "Tenant 1", access_rules=[f"aihub.admin.agent.{AGENT_CLASS}"]
    )
    RoleEntity.create_tenant_role("BroadAgentAdmin", "desc", ["aihub.admin.agent.>"], TENANT_ID)
    UserTenantRoleEntity.create_or_update(USER_ID, TENANT_ID, ["BroadAgentAdmin"], validate_roles=False)

    assert not AccessChecker.from_user(_current_user()).has_access_to_agent(AGENT_CLASS, AGENT_ID)

    _grant_creator_access()
    assert AccessChecker.from_user(_current_user()).has_access_to_agent(AGENT_CLASS, AGENT_ID)

    _cleanup_instance_access()
    assert not AccessChecker.from_user(_current_user()).has_access_to_agent(AGENT_CLASS, AGENT_ID)


def test_user_role_is_the_blocker_and_per_instance_role_unblocks() -> None:
    """Tenant ceiling is broad; the narrow user role blocks the instance until the per-instance role is assigned."""
    TenantMetadataEntity.create_tenant_metadata(TENANT_ID, "Tenant 1", access_rules=["aihub.admin.>"])
    RoleEntity.create_tenant_role("NarrowAdmin", "desc", [f"aihub.admin.agent.{AGENT_CLASS}"], TENANT_ID)
    UserTenantRoleEntity.create_or_update(USER_ID, TENANT_ID, ["NarrowAdmin"], validate_roles=False)

    assert not AccessChecker.from_user(_current_user()).has_access_to_agent(AGENT_CLASS, AGENT_ID)

    _grant_creator_access()
    assert AccessChecker.from_user(_current_user()).has_access_to_agent(AGENT_CLASS, AGENT_ID)

    _cleanup_instance_access()
    assert not AccessChecker.from_user(_current_user()).has_access_to_agent(AGENT_CLASS, AGENT_ID)


def test_grant_is_idempotent_on_recreate() -> None:
    """Re-running the grant (e.g. create logic runs again) adds no duplicate rule or role."""
    TenantMetadataEntity.create_tenant_metadata(
        TENANT_ID, "Tenant 1", access_rules=[f"aihub.admin.agent.{AGENT_CLASS}"]
    )
    RoleEntity.create_tenant_role("BroadAgentAdmin", "desc", ["aihub.admin.agent.>"], TENANT_ID)
    UserTenantRoleEntity.create_or_update(USER_ID, TENANT_ID, ["BroadAgentAdmin"], validate_roles=False)

    _grant_creator_access()
    _grant_creator_access()

    tenant = TenantMetadataEntity.get_metadata_by_tenant_id(TENANT_ID)
    assert tenant.access_rules.count(ADMIN_RULE) == 1
    assert RoleEntity.objects(name=ROLE_NAME, tenant_id=TENANT_ID).count() == 1
    assert UserTenantRoleEntity.get_roles_for_user_in_tenant(USER_ID, TENANT_ID).count(ROLE_NAME) == 1
