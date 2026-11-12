import pytest

from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity

pytestmark = pytest.mark.beanie


class TestGrantAccessRule:
    async def test_appends_rule(self) -> None:
        await TenantMetadataEntity.create_tenant_metadata("t1", "Tenant 1", access_rules=["aihub.admin.agent.MyAgent"])

        await TenantMetadataEntity.grant_access_rule("t1", "aihub.admin.agent.MyAgent.inst1")

        tenant = await TenantMetadataEntity.get_metadata_by_tenant_id("t1")
        assert "aihub.admin.agent.MyAgent.inst1" in tenant.access_rules

    async def test_is_idempotent(self) -> None:
        await TenantMetadataEntity.create_tenant_metadata(
            "t1", "Tenant 1", access_rules=["aihub.admin.agent.MyAgent.inst1"]
        )

        await TenantMetadataEntity.grant_access_rule("t1", "aihub.admin.agent.MyAgent.inst1")

        tenant = await TenantMetadataEntity.get_metadata_by_tenant_id("t1")
        assert tenant.access_rules.count("aihub.admin.agent.MyAgent.inst1") == 1

    async def test_raises_when_tenant_metadata_missing(self) -> None:
        with pytest.raises(ValueError):
            await TenantMetadataEntity.grant_access_rule("missing", "aihub.admin.agent.MyAgent.inst1")


class TestRevokeAccessRuleFromAllTenants:
    async def test_removes_rule_from_every_tenant(self) -> None:
        rule = "aihub.admin.agent.MyAgent.inst1"
        await TenantMetadataEntity.create_tenant_metadata(
            "t1", "Tenant 1", access_rules=[rule, "aihub.admin.agent.MyAgent"]
        )
        await TenantMetadataEntity.create_tenant_metadata("t2", "Tenant 2", access_rules=[rule])
        await TenantMetadataEntity.create_tenant_metadata("t3", "Tenant 3", access_rules=["aihub.admin.>"])

        await TenantMetadataEntity.revoke_access_rule_from_all_tenants([rule])

        assert (await TenantMetadataEntity.get_metadata_by_tenant_id("t1")).access_rules == [
            "aihub.admin.agent.MyAgent"
        ]
        assert (await TenantMetadataEntity.get_metadata_by_tenant_id("t2")).access_rules == []
        assert (await TenantMetadataEntity.get_metadata_by_tenant_id("t3")).access_rules == ["aihub.admin.>"]

    async def test_is_noop_when_no_tenant_holds_the_rule(self) -> None:
        await TenantMetadataEntity.create_tenant_metadata("t1", "Tenant 1", access_rules=["aihub.admin.>"])

        await TenantMetadataEntity.revoke_access_rule_from_all_tenants(["aihub.admin.agent.Gone.gone"])

        assert (await TenantMetadataEntity.get_metadata_by_tenant_id("t1")).access_rules == ["aihub.admin.>"]


class TestDeleteRoleFromAllTenants:
    async def test_deletes_role_and_unassigns_users(self) -> None:
        role_name = "agent-MyAgent-inst1-admin"
        await RoleEntity.create_tenant_role(role_name, "desc", ["aihub.admin.agent.MyAgent.inst1"], "t1")
        await RoleEntity.create_tenant_role(role_name, "desc", ["aihub.admin.agent.MyAgent.inst1"], "t2")
        await UserTenantRoleEntity.create_or_update("user1", "t1", [role_name], validate_roles=False)

        removed = await RoleEntity.delete_role_from_all_tenants(role_name)

        assert removed == 2
        assert await RoleEntity.find({"name": role_name}).count() == 0
        assert await UserTenantRoleEntity.get_roles_for_user_in_tenant("user1", "t1") == []

    async def test_returns_zero_when_role_absent(self) -> None:
        assert await RoleEntity.delete_role_from_all_tenants("agent-Gone-gone-admin") == 0
