"""What the Beanie port of the access entities promises about storage (#1963).

These rows decide who may do what, so a write that drops a field or changes a name the previous release reads is a
security bug, not a cosmetic one. The previous release reads with MongoEngine documents, so the readback tests use
replicas of them rather than trusting the shape by inspection.
"""

from datetime import UTC, datetime, timedelta

import pytest
from mongoengine import DateTimeField, Document, IntField, ListField, StringField, connect, disconnect
from pymongo.asynchronous.database import AsyncDatabase

from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.persistence.access.access_change_hook import AccessChangeHook
from swiss_ai_hub.core.persistence.access.entities.bearer_token import BearerToken
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity, UsageLimit
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity

pytestmark = pytest.mark.beanie

PREVIOUS_RELEASE_ALIAS = "previous_release_access"


class PreviousReleaseBearerToken(Document):
    """`BearerToken` as MongoEngine declared it before the port, strict like the original's fields."""

    meta = {"collection": "tokens", "db_alias": PREVIOUS_RELEASE_ALIAS}

    version = IntField(default=1, db_field="_version")
    user_oid = StringField(required=True)
    name = StringField(required=True)
    token = StringField(required=True)
    expiry_date = DateTimeField(required=True)


class PreviousReleaseUserTenantRole(Document):
    meta = {"collection": "user_tenant_roles", "db_alias": PREVIOUS_RELEASE_ALIAS}

    user_id = StringField(required=True)
    tenant_id = StringField(required=True)
    roles = ListField(StringField(), default=list)
    created_at = DateTimeField()
    updated_at = DateTimeField()


@pytest.fixture
def previous_release():
    connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
        alias=PREVIOUS_RELEASE_ALIAS,
    )
    yield
    disconnect(alias=PREVIOUS_RELEASE_ALIAS)


async def test_a_token_stores_its_version_under_the_previous_field_name(beanie_test_database: AsyncDatabase):
    token = await BearerToken.create_new_token("ci", datetime.now(UTC) + timedelta(days=1), "user-1")

    stored = await beanie_test_database["tokens"].find_one({"_id": token.id})

    assert stored["_version"] == 1
    assert "version" not in stored


async def test_the_previous_release_reads_a_token_this_one_wrote(previous_release):
    token = await BearerToken.create_new_token("ci", datetime.now(UTC) + timedelta(days=1), "user-1")

    read_back = PreviousReleaseBearerToken.objects(token=token.token).first()

    assert read_back.user_oid == "user-1"
    assert read_back.version == 1


async def test_a_token_written_by_the_previous_release_still_verifies(previous_release):
    PreviousReleaseBearerToken(
        user_oid="user-2", name="legacy", token="sk-legacy-token", expiry_date=datetime.now() + timedelta(days=1)
    ).save()

    token = await BearerToken.verify_token("sk-legacy-token")

    assert token.user_oid == "user-2"
    assert token.version == 1


async def test_rotating_the_static_token_keeps_fields_the_model_does_not_declare(
    beanie_test_database: AsyncDatabase,
):
    expiry = datetime.now(UTC) + timedelta(days=1)
    token = await BearerToken.upsert_static_token("superuser", "sk-first", expiry, "admin")
    await beanie_test_database["tokens"].update_one({"_id": token.id}, {"$set": {"issued_by": "ops"}})

    await BearerToken.upsert_static_token("superuser", "sk-second", expiry, "admin")

    stored = await beanie_test_database["tokens"].find_one({"_id": token.id})
    assert stored["token"] == "sk-second"
    assert stored["issued_by"] == "ops"


async def test_changing_roles_keeps_fields_the_model_does_not_declare(beanie_test_database: AsyncDatabase):
    await RoleEntity.create_tenant_role("Reader", "Reads", ["aihub.user.agent.>"], "tenant-1")
    await RoleEntity.create_tenant_role("Writer", "Writes", ["aihub.admin.agent.>"], "tenant-1")
    association = await UserTenantRoleEntity.create_or_update("user-1", "tenant-1", ["Reader"])
    await beanie_test_database["user_tenant_roles"].update_one({"_id": association.id}, {"$set": {"granted_by": "sso"}})

    await UserTenantRoleEntity.add_roles("user-1", "tenant-1", ["Writer"])

    stored = await beanie_test_database["user_tenant_roles"].find_one({"_id": association.id})
    assert sorted(stored["roles"]) == ["Reader", "Writer"]
    assert stored["granted_by"] == "sso"


async def test_the_previous_release_reads_a_membership_this_one_wrote(previous_release):
    await RoleEntity.create_tenant_role("Reader", "Reads", [], "tenant-1")
    await UserTenantRoleEntity.create_or_update("user-1", "tenant-1", ["Reader"])

    read_back = PreviousReleaseUserTenantRole.objects(user_id="user-1", tenant_id="tenant-1").first()

    assert read_back.roles == ["Reader"]


async def test_tenant_metadata_keeps_its_slug_as_the_id(beanie_test_database: AsyncDatabase):
    await TenantMetadataEntity.create_tenant_metadata("acme", "ACME")

    stored = await beanie_test_database["tenants"].find_one({"_id": "acme"})

    assert stored["name"] == "ACME"
    assert (await TenantMetadataEntity.get_metadata_by_tenant_id("acme")).name == "ACME"


async def test_a_role_with_a_duplicate_usage_limit_is_not_saved():
    role = await RoleEntity.create_tenant_role("Capped", "Capped", [], "tenant-1")
    role.usage_limits = [
        UsageLimit(pattern="agent.>", limit=5, period="1d"),
        UsageLimit(pattern="agent.>", limit=9, period="1d"),
    ]

    with pytest.raises(ValueError, match="Duplicate usage limit"):
        await role.save_changes()

    assert (await RoleEntity.get_role("Capped", "tenant-1")).usage_limits == []


@pytest.mark.parametrize(
    "change",
    ["role", "tenant", "membership", "tenant_cascade"],
)
async def test_every_access_change_asks_openwebui_to_resync(change: str, monkeypatch: pytest.MonkeyPatch):
    await TenantMetadataEntity.create_tenant_metadata("acme", "ACME")
    await RoleEntity.create_tenant_role("Reader", "Reads", [], "acme")
    notified: list[bool] = []
    monkeypatch.setattr(AccessChangeHook, "notify", lambda: notified.append(True))

    match change:
        case "role":
            await RoleEntity.update_role("Reader", "acme", access_rules=["aihub.user.>"])
        case "tenant":
            await TenantMetadataEntity.grant_access_rule("acme", "aihub.user.agent.>")
        case "membership":
            await UserTenantRoleEntity.create_or_update("user-1", "acme", ["Reader"])
        case "tenant_cascade":
            await TenantMetadataEntity.cascade_delete_tenant_data("acme")

    assert notified
