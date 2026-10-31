from collections.abc import AsyncIterator
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI, HTTPException, Request
from keycloak import KeycloakGetError
from swiss_ai_hub.api import ApiLocaleString
from swiss_ai_hub.core.auth import KeycloakAdminService, UserIdentity
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.persistence import TenantMetadataEntity

from swiss_ai_hub.sysadmin_api.routes.tenant_admin.tenant_admin_controller import TenantAdminController

pytestmark = pytest.mark.beanie

ADMIN = {"x-test-role": "sysadmin"}


async def stored(tenant_id: str) -> TenantMetadataEntity | None:
    return await TenantMetadataEntity.get(tenant_id)


@pytest_asyncio.fixture(loop_scope="session")
async def client(clean_beanie_collections: None) -> AsyncIterator[httpx.AsyncClient]:
    for tenant_id in ("one", "two", "orphaned"):
        await TenantMetadataEntity.create_tenant_metadata(
            tenant_id, tenant_id, description="Original", access_rules=["aihub.admin.>"]
        )

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
        # The conftest's `mock_tenant_entity` answers every tenant id with one fake tenant; these tests read the
        # rows they wrote.
        patch.object(TenantMetadataEntity, "get_metadata_by_tenant_id", new=AsyncMock(side_effect=stored)),
        patch.object(KeycloakAdminService, "get_tenant_group", side_effect=tenant_group),
        patch.object(KeycloakAdminService, "get_all_tenant_groups", side_effect=tenant_groups),
    ):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as test_client:
            yield test_client


async def test_only_sysadmins_can_read_and_write_disclaimer(client):
    route = "/admin/tenants/one"
    body = {"chat_disclaimer": {"en": "Verify answers."}}
    for role, status in ((None, 401), ("admin", 403), ("user", 403), ("chat-only", 403)):
        headers = {"x-test-role": role} if role else {}
        assert (await client.get(route, headers=headers)).status_code == status
        assert (await client.patch(route, headers=headers, json=body)).status_code == status
    assert (await stored("one")).chat_disclaimer is None


async def test_existing_tenant_without_disclaimer_uses_localized_defaults(client):
    defaults = ApiLocaleString.from_i18n_path("api.common.default_chat_disclaimer").model_dump()
    assert "chat_disclaimer" not in await TenantMetadataEntity.get_pymongo_collection().find_one({"_id": "one"})
    assert (await client.get("/admin/tenants/one", headers=ADMIN)).json()["chat_disclaimer"] == defaults
    response = await client.get("/admin/tenants/", headers=ADMIN)
    assert response.status_code == 200
    assert all(tenant["chat_disclaimer"] == defaults for tenant in response.json())
    assert (await stored("one")).chat_disclaimer is None


async def test_sysadmin_saves_disclaimer_with_other_metadata_for_selected_tenant(client):
    saved = await client.patch(
        "/admin/tenants/two",
        headers=ADMIN,
        json={
            "name": "Renamed",
            "description": "Updated description",
            "access_rules": ["aihub.user.service.openai"],
            "chat_disclaimer": {"de": "  Prüfen.  ", "en": "Verify.", "fr": " "},
        },
    )
    assert saved.status_code == 200
    assert saved.json()["chat_disclaimer"] == {"de": "Prüfen.", "en": "Verify.", "fr": None, "it": None}
    fetched = (await client.get("/admin/tenants/two", headers=ADMIN)).json()
    for field in ("name", "description", "access_rules", "chat_disclaimer"):
        assert fetched[field] == saved.json()[field]
    entity = await stored("two")
    assert entity.name == "Renamed"
    assert entity.description == "Updated description"
    assert entity.access_rules == ["aihub.user.service.openai"]
    assert entity.chat_disclaimer.en == "Verify."
    assert (await stored("one")).chat_disclaimer is None


@pytest.mark.parametrize("body", [{"description": "Changed"}, {"chat_disclaimer": None}])
async def test_unrelated_updates_preserve_disclaimer(client, body):
    await TenantMetadataEntity.update_tenant_metadata("one", chat_disclaimer=LocaleString(en="Verify."))
    response = await client.patch("/admin/tenants/one", headers=ADMIN, json=body)
    assert response.status_code == 200
    assert response.json()["chat_disclaimer"]["en"] == "Verify."
    assert (await stored("one")).chat_disclaimer.en == "Verify."


async def test_unknown_and_orphaned_tenants_cannot_be_edited(client):
    body = {"chat_disclaimer": {"en": "Verify."}}
    assert (await client.patch("/admin/tenants/missing", headers=ADMIN, json=body)).status_code == 404
    assert await stored("missing") is None
    assert (await client.get("/admin/tenants/orphaned", headers=ADMIN)).status_code == 200
    assert (await client.patch("/admin/tenants/orphaned", headers=ADMIN, json=body)).status_code == 409
    assert (await stored("orphaned")).chat_disclaimer is None


@pytest.mark.parametrize(
    "text", [{}, {"en": " \n "}, {"en": "x" * 101}, {"en": "🙂" * 101}, {"en": "Valid", "fr": "x" * 101}]
)
async def test_invalid_disclaimer_prevents_entire_metadata_update(client, text):
    response = await client.patch(
        "/admin/tenants/one",
        headers=ADMIN,
        json={"name": "Must not persist", "chat_disclaimer": text},
    )
    assert response.status_code == 422
    entity = await stored("one")
    assert entity.name == "one"
    assert entity.chat_disclaimer is None


async def test_disclaimer_limit_counts_unicode_characters(client):
    text = "🙂" * 100
    response = await client.patch("/admin/tenants/one", headers=ADMIN, json={"chat_disclaimer": {"en": text}})
    assert response.status_code == 200
    assert (await stored("one")).chat_disclaimer.en == text


async def test_saved_disclaimer_above_current_limit_can_be_read_and_shortened(client):
    text = "x" * 314
    await TenantMetadataEntity.update_tenant_metadata("one", chat_disclaimer=LocaleString(en=text))
    response = await client.get("/admin/tenants/one", headers=ADMIN)
    assert response.status_code == 200
    assert response.json()["chat_disclaimer"]["en"] == text
    too_long = await client.patch("/admin/tenants/one", headers=ADMIN, json={"chat_disclaimer": {"en": text}})
    assert too_long.status_code == 422
    assert (await stored("one")).chat_disclaimer.en == text
    saved = await client.patch("/admin/tenants/one", headers=ADMIN, json={"chat_disclaimer": {"en": "Verify answers."}})
    assert saved.status_code == 200
    assert saved.json()["chat_disclaimer"]["en"] == "Verify answers."
    assert (await stored("one")).chat_disclaimer.en == "Verify answers."


async def test_deleting_tenant_removes_disclaimer_with_metadata(client):
    for tenant in ("one", "two"):
        await TenantMetadataEntity.update_tenant_metadata(tenant, chat_disclaimer=LocaleString(en=tenant))
    response = await client.delete("/admin/tenants/one", headers=ADMIN)
    assert response.status_code == 204
    assert await stored("one") is None
    assert (await stored("two")).chat_disclaimer.en == "two"
