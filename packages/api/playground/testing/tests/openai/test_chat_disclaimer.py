from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from mongoengine import connect, disconnect
from swiss_ai_hub.core.auth import AuthHandler, UserIdentity
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import AIHubSettings, MongoSettings
from swiss_ai_hub.core.persistence import TenantMetadataEntity

from swiss_ai_hub.api.i18n.middleware.i18n_middleware import I18nMiddleware
from swiss_ai_hub.api.routes.openai.openai_controller import OpenaiController


@pytest.fixture
def client():
    connect(db=AIHubSettings().MONGO_MAIN_DB_NAME, host=MongoSettings().CONNECTION_STRING.get_secret_value())
    TenantMetadataEntity.drop_collection()

    for tenant_id in ("one", "two"):
        TenantMetadataEntity(id=tenant_id, name=tenant_id, access_rules=["aihub.admin.>"]).save()

    async def authenticate(request: Request) -> UserIdentity:
        role = request.headers.get("x-test-role")
        if not role:
            raise HTTPException(status_code=401)
        tenant = await AuthHandler.resolve_tenant_for_user(request, "test-user")
        return UserIdentity(
            id="test-user", name="Test", email="test@example.com", roles=[role], acting_within_tenant=tenant
        )

    def metadata(tenant_id):
        return TenantMetadataEntity.objects(id=tenant_id).first()

    rules = {
        "chat-only": ["aihub.user.service.openai"],
        "denied": [],
    }
    app = FastAPI()
    app.add_middleware(I18nMiddleware)
    OpenaiController(auth=authenticate).get_chat_disclaimer().mount(app, SimpleNamespace())
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
    TenantMetadataEntity.drop_collection()
    disconnect()


@pytest.mark.parametrize("language", ["de", "en", "fr", "it"])
def test_default_disclaimer_is_localized(client, language):
    from swiss_ai_hub.api.i18n.api_locale_string import ApiLocaleString

    response = client.get("/one/openai/chat-disclaimer", headers={"x-test-role": "chat-only", "lang": language})
    assert response.status_code == 200
    assert response.json() == ApiLocaleString.from_i18n_path("api.common.default_chat_disclaimer").in_locale(language)
    assert TenantMetadataEntity.objects.get(id="one").chat_disclaimer is None


def test_chat_disclaimer_requires_chat_access(client):
    assert client.get("/one/openai/chat-disclaimer").status_code == 401
    assert client.get("/one/openai/chat-disclaimer", headers={"x-test-role": "denied"}).status_code == 403
    assert client.get("/outside/openai/chat-disclaimer", headers={"x-test-role": "chat-only"}).status_code == 403


def test_saved_disclaimer_localization_and_tenant_isolation(client):
    TenantMetadataEntity.update_tenant_metadata("one", chat_disclaimer=LocaleString(de="Prüfen.", en="Verify."))
    headers = {"x-test-role": "chat-only"}
    assert client.get("/one/openai/chat-disclaimer", headers={**headers, "lang": "fr"}).json() == "Prüfen."
    assert client.get("/one/openai/chat-disclaimer", headers={**headers, "lang": "en"}).json() == "Verify."
    assert (
        client.get("/two/openai/chat-disclaimer", headers={**headers, "lang": "en"}).json()
        == "AI can make mistakes. Please verify answers."
    )
    TenantMetadataEntity.update_tenant_metadata("one", chat_disclaimer=LocaleString(it="Verifica."))
    assert client.get("/one/openai/chat-disclaimer", headers={**headers, "lang": "en"}).json() == "Verifica."
