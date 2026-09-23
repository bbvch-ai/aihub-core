from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from mongoengine import connect, disconnect
from swiss_ai_hub.core.auth import AuthHandler, UserIdentity
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import AIHubSettings, MongoSettings
from swiss_ai_hub.core.persistence import TenantMetadataEntity, TenantSettingsEntity

from swiss_ai_hub.api.i18n.middleware.i18n_middleware import I18nMiddleware
from swiss_ai_hub.api.routes.openai.openai_controller import OpenaiController
from swiss_ai_hub.api.routes.suite.suite_controller import SuiteController
from swiss_ai_hub.api.routes.tenant_settings.tenant_settings_controller import TenantSettingsController


@pytest.fixture
def client():
    """Use MongoDB with stubbed authentication and tenant access."""
    connect(db=AIHubSettings().MONGO_MAIN_DB_NAME, host=MongoSettings().CONNECTION_STRING.get_secret_value())
    TenantSettingsEntity.drop_collection()

    async def authenticate(request: Request) -> UserIdentity:
        role = request.headers.get("x-test-role")
        if not role:
            raise HTTPException(status_code=401)
        tenant = await AuthHandler.resolve_tenant_for_user(request, "test-user")
        return UserIdentity(
            id="test-user", name="Test", email="test@example.com", roles=[role], acting_within_tenant=tenant
        )

    def metadata(tenant_id):
        return SimpleNamespace(id=tenant_id, name=tenant_id, access_rules=["aihub.admin.>"])

    rules = {
        "admin": ["aihub.admin.>"],
        "user": ["aihub.user.>"],
        "chat-only": ["aihub.user.service.openai"],
        "denied": [],
    }
    app = FastAPI()
    app.add_middleware(I18nMiddleware)
    controllers = [
        TenantSettingsController(auth=authenticate).get_tenant_settings().update_tenant_settings(),
        OpenaiController(auth=authenticate).get_chat_disclaimer(),
    ]
    runner = SimpleNamespace(controllers=controllers)
    for controller in controllers:
        controller.mount(app, runner)
    SuiteController(auth=authenticate).get_suite().mount(app, runner)
    with (
        patch.object(TenantMetadataEntity, "get_metadata_by_tenant_id", side_effect=metadata),
        patch(
            "swiss_ai_hub.core.auth.keycloak.keycloak_admin_service.KeycloakAdminService.is_user_member_of_tenant",
            new=AsyncMock(side_effect=lambda user_id, tenant_id: tenant_id in {"one", "two"}),
        ),
        patch(
            "swiss_ai_hub.core.persistence.access.entities.role_entity.RoleEntity.get_access_rules_for_roles",
            side_effect=lambda roles, **kwargs: rules[roles[0]],
        ),
        TestClient(app) as test_client,
    ):
        yield test_client
    TenantSettingsEntity.drop_collection()
    disconnect()


def test_default_translations_and_admin_write_permissions(client):
    admin = {"x-test-role": "admin"}
    settings = client.get("/one/tenant-settings", headers=admin)
    assert settings.status_code == 200
    defaults = settings.json()["chat_disclaimer"]
    for language in ("de", "en", "fr", "it"):
        response = client.get("/one/openai/chat-disclaimer", headers={"x-test-role": "user", "lang": language})
        assert response.status_code == 200
        assert response.json() == defaults[language]
        assert response.json()

    assert client.get("/one/tenant-settings").status_code == 401
    assert client.get("/one/tenant-settings", headers={"x-test-role": "user"}).status_code == 403
    assert client.put("/one/tenant-settings", headers={"x-test-role": "user"}, json=settings.json()).status_code == 403
    assert client.get("/one/openai/chat-disclaimer", headers={"x-test-role": "denied"}).status_code == 403


def test_chat_only_user_can_read_disclaimer_without_settings_access(client):
    headers = {"x-test-role": "chat-only", "lang": "en"}
    response = client.get("/one/openai/chat-disclaimer", headers=headers)
    assert response.status_code == 200
    assert response.json() == "AI can make mistakes. Please verify answers."
    assert client.get("/one/tenant-settings", headers=headers).status_code == 403
    assert (
        client.put("/one/tenant-settings", headers=headers, json={"chat_disclaimer": {"en": "Changed"}}).status_code
        == 403
    )
    assert TenantSettingsEntity.get_chat_disclaimer("one") is None


def test_tenant_settings_menu_is_only_available_to_admins(client):
    for role, visible in (("admin", True), ("user", False)):
        response = client.get("/one/suites/", headers={"x-test-role": role})
        assert response.status_code == 200
        paths = [service["path"] for service in response.json()["services"]]
        assert ("/service/tenant-settings" in paths) is visible


def test_persistence_localization_fallback_and_tenant_isolation(client):
    admin = {"x-test-role": "admin"}
    body = {"chat_disclaimer": {"de": "  Prüfen.  ", "en": "Verify.", "fr": " ", "it": None}}
    saved = client.put("/one/tenant-settings", headers=admin, json=body)
    assert saved.status_code == 200
    assert saved.json()["chat_disclaimer"]["de"] == "Prüfen."
    assert saved.json()["chat_disclaimer"]["fr"] is None
    assert client.get("/one/tenant-settings", headers=admin).json() == saved.json()
    assert TenantSettingsEntity.get_chat_disclaimer("one").en == "Verify."
    assert client.get("/one/openai/chat-disclaimer", headers={**admin, "lang": "fr"}).json() == "Prüfen."
    assert client.get("/one/openai/chat-disclaimer", headers={**admin, "lang": "en"}).json() == "Verify."
    assert client.get("/two/tenant-settings", headers=admin).json() != saved.json()
    assert client.get("/outside/tenant-settings", headers=admin).status_code == 403
    assert client.put("/outside/tenant-settings", headers=admin, json=body).status_code == 403
    assert TenantSettingsEntity.get_chat_disclaimer("outside") is None

    # If German is absent too, use the first populated supported translation.
    client.put("/one/tenant-settings", headers=admin, json={"chat_disclaimer": {"it": "Verifica."}})
    assert client.get("/one/openai/chat-disclaimer", headers={**admin, "lang": "en"}).json() == "Verifica."


@pytest.mark.parametrize(
    "body",
    [
        {"chat_disclaimer": {}},
        {"chat_disclaimer": {"en": " \n "}},
        {"chat_disclaimer": {"en": "x" * 101}},
        {"chat_disclaimer": {"en": "🙂" * 101}},
        {"chat_disclaimer": {"en": "Valid"}, "tenant_id": "two"},
    ],
)
def test_invalid_settings_do_not_persist(client, body):
    assert client.put("/one/tenant-settings", headers={"x-test-role": "admin"}, json=body).status_code == 422
    assert TenantSettingsEntity.get_chat_disclaimer("one") is None


def test_disclaimer_limit_counts_unicode_characters(client):
    text = "🙂" * 100
    response = client.put(
        "/one/tenant-settings", headers={"x-test-role": "admin"}, json={"chat_disclaimer": {"en": text}}
    )
    assert response.status_code == 200
    assert TenantSettingsEntity.get_chat_disclaimer("one").en == text


def test_saved_disclaimer_above_current_limit_can_be_read_and_shortened(client):
    text = "x" * 314
    TenantSettingsEntity.set_chat_disclaimer("one", LocaleString(en=text))
    admin = {"x-test-role": "admin"}
    response = client.get("/one/tenant-settings", headers=admin)
    assert response.status_code == 200
    assert response.json()["chat_disclaimer"]["en"] == text
    assert client.put("/one/tenant-settings", headers=admin, json=response.json()).status_code == 422
    assert TenantSettingsEntity.get_chat_disclaimer("one").en == text

    shortened = {"chat_disclaimer": {"en": "Verify answers."}}
    saved = client.put("/one/tenant-settings", headers=admin, json=shortened)
    assert saved.status_code == 200
    assert saved.json()["chat_disclaimer"]["en"] == "Verify answers."
    assert client.get("/one/tenant-settings", headers=admin).json() == saved.json()
    assert TenantSettingsEntity.get_chat_disclaimer("one").en == "Verify answers."


def test_deleting_a_tenant_removes_only_its_settings(client):
    for tenant in ("one", "two"):
        client.put(
            f"/{tenant}/tenant-settings", headers={"x-test-role": "admin"}, json={"chat_disclaimer": {"en": tenant}}
        )
    TenantMetadataEntity.cascade_delete_tenant_data("one")
    assert TenantSettingsEntity.get_chat_disclaimer("one") is None
    assert TenantSettingsEntity.get_chat_disclaimer("two").en == "two"
