from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from keycloak import KeycloakGetError
from mongoengine import connect, disconnect
from swiss_ai_hub.api import ApiLocaleString
from swiss_ai_hub.core.auth import KeycloakAdminService, UserIdentity
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import AIHubSettings, MongoSettings
from swiss_ai_hub.core.persistence import TenantMetadataEntity

from swiss_ai_hub.sysadmin_api.routes.tenant_admin.tenant_admin_controller import TenantAdminController


@pytest.fixture
def client():
    connect(db=AIHubSettings().MONGO_MAIN_DB_NAME, host=MongoSettings().CONNECTION_STRING.get_secret_value())
    TenantMetadataEntity.drop_collection()
    for tenant_id in ("one", "two", "orphaned"):
        TenantMetadataEntity(
            id=tenant_id, name=tenant_id, description="Original", access_rules=["aihub.admin.>"]
        ).save()

    async def authenticate(request: Request) -> UserIdentity:
        role = request.headers.get("x-test-role")
        if not role:
            raise HTTPException(status_code=401)
        return UserIdentity(
            id="test-user",
            name="Test",
            email="test@example.com",
            roles=[role],
            is_sys_admin=role == "sysadmin",
            acting_within_tenant={"id": "one", "name": "one", "access_rules": ["aihub.admin.>"]},
        )

    async def tenant_group(tenant_id):
        if tenant_id == "orphaned":
            raise KeycloakGetError("Missing group", response_code=404)
        return SimpleNamespace(name=tenant_id)

    async def tenant_groups():
        return [SimpleNamespace(name=tenant_id) for tenant_id in ("one", "two")]

    app = FastAPI()
    (
        TenantAdminController(auth=authenticate)
        .list_tenants()
        .get_tenant()
        .update_tenant_metadata()
        .delete_tenant_metadata()
        .mount(app, SimpleNamespace())
    )
    with (
        patch.object(
            TenantMetadataEntity,
            "get_metadata_by_tenant_id",
            side_effect=lambda tenant_id: TenantMetadataEntity.objects(id=tenant_id).first(),
        ),
        patch.object(KeycloakAdminService, "get_tenant_group", side_effect=tenant_group),
        patch.object(KeycloakAdminService, "get_all_tenant_groups", side_effect=tenant_groups),
        TestClient(app) as test_client,
    ):
        yield test_client
    TenantMetadataEntity.drop_collection()
    disconnect()


def test_only_sysadmins_can_read_and_write_disclaimer(client):
    route = "/admin/tenants/one"
    body = {"chat_disclaimer": {"en": "Verify answers."}}
    for role, status in ((None, 401), ("admin", 403), ("user", 403), ("chat-only", 403)):
        headers = {"x-test-role": role} if role else {}
        assert client.get(route, headers=headers).status_code == status
        assert client.patch(route, headers=headers, json=body).status_code == status
    assert TenantMetadataEntity.objects.get(id="one").chat_disclaimer is None


def test_existing_tenant_without_disclaimer_uses_localized_defaults(client):
    admin = {"x-test-role": "sysadmin"}
    defaults = ApiLocaleString.from_i18n_path("api.common.default_chat_disclaimer").model_dump()
    assert "chat_disclaimer" not in TenantMetadataEntity.objects.get(id="one").to_mongo()
    assert client.get("/admin/tenants/one", headers=admin).json()["chat_disclaimer"] == defaults
    response = client.get("/admin/tenants/", headers=admin)
    assert response.status_code == 200
    assert all(tenant["chat_disclaimer"] == defaults for tenant in response.json())
    assert TenantMetadataEntity.objects.get(id="one").chat_disclaimer is None


def test_sysadmin_saves_disclaimer_with_other_metadata_for_selected_tenant(client):
    admin = {"x-test-role": "sysadmin"}
    saved = client.patch(
        "/admin/tenants/two",
        headers=admin,
        json={
            "name": "Renamed",
            "description": "Updated description",
            "access_rules": ["aihub.user.service.openai"],
            "chat_disclaimer": {"de": "  Prüfen.  ", "en": "Verify.", "fr": " "},
        },
    )
    assert saved.status_code == 200
    assert saved.json()["chat_disclaimer"] == {"de": "Prüfen.", "en": "Verify.", "fr": None, "it": None}
    fetched = client.get("/admin/tenants/two", headers=admin).json()
    for field in ("name", "description", "access_rules", "chat_disclaimer"):
        assert fetched[field] == saved.json()[field]
    entity = TenantMetadataEntity.objects.get(id="two")
    assert entity.name == "Renamed"
    assert entity.description == "Updated description"
    assert entity.access_rules == ["aihub.user.service.openai"]
    assert entity.chat_disclaimer.en == "Verify."
    assert TenantMetadataEntity.objects.get(id="one").chat_disclaimer is None


@pytest.mark.parametrize("body", [{"description": "Changed"}, {"chat_disclaimer": None}])
def test_unrelated_updates_preserve_disclaimer(client, body):
    TenantMetadataEntity.update_tenant_metadata("one", chat_disclaimer=LocaleString(en="Verify."))
    response = client.patch("/admin/tenants/one", headers={"x-test-role": "sysadmin"}, json=body)
    assert response.status_code == 200
    assert response.json()["chat_disclaimer"]["en"] == "Verify."
    assert TenantMetadataEntity.objects.get(id="one").chat_disclaimer.en == "Verify."


def test_unknown_and_orphaned_tenants_cannot_be_edited(client):
    admin = {"x-test-role": "sysadmin"}
    body = {"chat_disclaimer": {"en": "Verify."}}
    assert client.patch("/admin/tenants/missing", headers=admin, json=body).status_code == 404
    assert TenantMetadataEntity.objects(id="missing").first() is None
    assert client.get("/admin/tenants/orphaned", headers=admin).status_code == 200
    assert client.patch("/admin/tenants/orphaned", headers=admin, json=body).status_code == 409
    assert TenantMetadataEntity.objects.get(id="orphaned").chat_disclaimer is None


@pytest.mark.parametrize(
    "text", [{}, {"en": " \n "}, {"en": "x" * 101}, {"en": "🙂" * 101}, {"en": "Valid", "fr": "x" * 101}]
)
def test_invalid_disclaimer_prevents_entire_metadata_update(client, text):
    response = client.patch(
        "/admin/tenants/one",
        headers={"x-test-role": "sysadmin"},
        json={"name": "Must not persist", "chat_disclaimer": text},
    )
    assert response.status_code == 422
    entity = TenantMetadataEntity.objects.get(id="one")
    assert entity.name == "one"
    assert entity.chat_disclaimer is None


def test_disclaimer_limit_counts_unicode_characters(client):
    text = "🙂" * 100
    response = client.patch(
        "/admin/tenants/one", headers={"x-test-role": "sysadmin"}, json={"chat_disclaimer": {"en": text}}
    )
    assert response.status_code == 200
    assert TenantMetadataEntity.objects.get(id="one").chat_disclaimer.en == text


def test_saved_disclaimer_above_current_limit_can_be_read_and_shortened(client):
    text = "x" * 314
    TenantMetadataEntity.update_tenant_metadata("one", chat_disclaimer=LocaleString(en=text))
    admin = {"x-test-role": "sysadmin"}
    response = client.get("/admin/tenants/one", headers=admin)
    assert response.status_code == 200
    assert response.json()["chat_disclaimer"]["en"] == text
    assert client.patch("/admin/tenants/one", headers=admin, json={"chat_disclaimer": {"en": text}}).status_code == 422
    assert TenantMetadataEntity.objects.get(id="one").chat_disclaimer.en == text
    saved = client.patch("/admin/tenants/one", headers=admin, json={"chat_disclaimer": {"en": "Verify answers."}})
    assert saved.status_code == 200
    assert saved.json()["chat_disclaimer"]["en"] == "Verify answers."
    assert TenantMetadataEntity.objects.get(id="one").chat_disclaimer.en == "Verify answers."


def test_deleting_tenant_removes_disclaimer_with_metadata(client):
    for tenant in ("one", "two"):
        TenantMetadataEntity.update_tenant_metadata(tenant, chat_disclaimer=LocaleString(en=tenant))
    response = client.delete("/admin/tenants/one", headers={"x-test-role": "sysadmin"})
    assert response.status_code == 204
    assert TenantMetadataEntity.objects(id="one").first() is None
    assert TenantMetadataEntity.objects.get(id="two").chat_disclaimer.en == "two"
