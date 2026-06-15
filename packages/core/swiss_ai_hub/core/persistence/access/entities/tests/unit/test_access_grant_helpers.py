from collections.abc import Generator

import pytest
from mongoengine import connect, disconnect

from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity


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
    TenantMetadataEntity.objects.delete()
    RoleEntity.objects.delete()
    UserTenantRoleEntity.objects.delete()
    yield
    TenantMetadataEntity.objects.delete()
    RoleEntity.objects.delete()
    UserTenantRoleEntity.objects.delete()


class TestGrantAccessRule:
    def test_appends_rule(self) -> None:
        TenantMetadataEntity.create_tenant_metadata("t1", "Tenant 1", access_rules=["aihub.admin.agent.MyAgent"])

        TenantMetadataEntity.grant_access_rule("t1", "aihub.admin.agent.MyAgent.inst1")

        tenant = TenantMetadataEntity.get_metadata_by_tenant_id("t1")
        assert "aihub.admin.agent.MyAgent.inst1" in tenant.access_rules

    def test_is_idempotent(self) -> None:
        TenantMetadataEntity.create_tenant_metadata("t1", "Tenant 1", access_rules=["aihub.admin.agent.MyAgent.inst1"])

        TenantMetadataEntity.grant_access_rule("t1", "aihub.admin.agent.MyAgent.inst1")

        tenant = TenantMetadataEntity.get_metadata_by_tenant_id("t1")
        assert tenant.access_rules.count("aihub.admin.agent.MyAgent.inst1") == 1

    def test_raises_when_tenant_metadata_missing(self) -> None:
        with pytest.raises(ValueError):
            TenantMetadataEntity.grant_access_rule("missing", "aihub.admin.agent.MyAgent.inst1")


class TestRevokeAccessRuleFromAllTenants:
    def test_removes_rule_from_every_tenant(self) -> None:
        rule = "aihub.admin.agent.MyAgent.inst1"
        TenantMetadataEntity.create_tenant_metadata("t1", "Tenant 1", access_rules=[rule, "aihub.admin.agent.MyAgent"])
        TenantMetadataEntity.create_tenant_metadata("t2", "Tenant 2", access_rules=[rule])
        TenantMetadataEntity.create_tenant_metadata("t3", "Tenant 3", access_rules=["aihub.admin.>"])

        TenantMetadataEntity.revoke_access_rule_from_all_tenants([rule])

        assert TenantMetadataEntity.get_metadata_by_tenant_id("t1").access_rules == ["aihub.admin.agent.MyAgent"]
        assert TenantMetadataEntity.get_metadata_by_tenant_id("t2").access_rules == []
        assert TenantMetadataEntity.get_metadata_by_tenant_id("t3").access_rules == ["aihub.admin.>"]


class TestDeleteRoleFromAllTenants:
    def test_deletes_role_and_unassigns_users(self) -> None:
        role_name = "agent-MyAgent-inst1-admin"
        RoleEntity.create_tenant_role(role_name, "desc", ["aihub.admin.agent.MyAgent.inst1"], "t1")
        RoleEntity.create_tenant_role(role_name, "desc", ["aihub.admin.agent.MyAgent.inst1"], "t2")
        UserTenantRoleEntity.create_or_update("user1", "t1", [role_name], validate_roles=False)

        removed = RoleEntity.delete_role_from_all_tenants(role_name)

        assert removed == 2
        assert RoleEntity.objects(name=role_name).count() == 0
        assert UserTenantRoleEntity.get_roles_for_user_in_tenant("user1", "t1") == []
