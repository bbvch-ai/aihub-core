from collections.abc import AsyncIterator
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI, HTTPException, Request
from swiss_ai_hub.core.auth import AuthHandler, UserIdentity
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.persistence import TenantMetadataEntity

from swiss_ai_hub.api.i18n.middleware.i18n_middleware import I18nMiddleware
from swiss_ai_hub.api.routes.openai.openai_controller import OpenaiController

pytestmark = pytest.mark.beanie


@pytest_asyncio.fixture(loop_scope="session")
async def client(clean_beanie_collections: None) -> AsyncIterator[httpx.AsyncClient]:
    for tenant_id in ("one", "two"):
        await TenantMetadataEntity.create_tenant_metadata(tenant_id, tenant_id, access_rules=["aihub.admin.>"])

    async def authenticate(request: Request) -> UserIdentity:
        role = request.headers.get("x-test-role")
        if not role:
            raise HTTPException(status_code=401)
        tenant = await AuthHandler.resolve_tenant_for_user(request, "test-user")
        return UserIdentity(
            id="test-user", name="Test", email="test@example.com", roles=[role], acting_within_tenant=tenant
        )

    rules = {
        "chat-only": ["aihub.user.service.openai"],
        "denied": [],
    }

    async def access_rules_for_roles(roles: list[str], **kwargs: str) -> list[str]:  # noqa: S7503
        return rules[roles[0]]

    async def metadata(tenant_id: str) -> TenantMetadataEntity | None:
        return await TenantMetadataEntity.get(tenant_id)

    app = FastAPI()
    app.add_middleware(I18nMiddleware)
    OpenaiController(auth=authenticate).get_chat_disclaimer().mount(app, SimpleNamespace())
    with (
        patch(
            "swiss_ai_hub.core.auth.keycloak.keycloak_admin_service.KeycloakAdminService.is_user_member_of_tenant",
            new=AsyncMock(side_effect=lambda user_id, tenant_id: tenant_id in {"one", "two"}),
        ),
        patch(
            "swiss_ai_hub.core.persistence.access.entities.role_entity.RoleEntity.get_access_rules_for_roles",
            new=AsyncMock(side_effect=access_rules_for_roles),
        ),
        # The conftest's `mock_tenant_entity` answers every tenant id with one fake tenant; these tests read the
        # rows they wrote.
        patch.object(TenantMetadataEntity, "get_metadata_by_tenant_id", new=AsyncMock(side_effect=metadata)),
    ):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as test_client:
            yield test_client


@pytest.mark.parametrize("language", ["de", "en", "fr", "it"])
async def test_default_disclaimer_is_localized(client, language):
    from swiss_ai_hub.api.i18n.api_locale_string import ApiLocaleString

    response = await client.get("/one/openai/chat-disclaimer", headers={"x-test-role": "chat-only", "lang": language})
    assert response.status_code == 200
    assert response.json() == ApiLocaleString.from_i18n_path("api.common.default_chat_disclaimer").in_locale(language)
    assert (await TenantMetadataEntity.get("one")).chat_disclaimer is None


async def test_chat_disclaimer_requires_chat_access(client):
    assert (await client.get("/one/openai/chat-disclaimer")).status_code == 401
    assert (await client.get("/one/openai/chat-disclaimer", headers={"x-test-role": "denied"})).status_code == 403
    assert (
        await client.get("/outside/openai/chat-disclaimer", headers={"x-test-role": "chat-only"})
    ).status_code == 403


async def test_saved_disclaimer_localization_and_tenant_isolation(client):
    await TenantMetadataEntity.update_tenant_metadata("one", chat_disclaimer=LocaleString(de="Prüfen.", en="Verify."))
    headers = {"x-test-role": "chat-only"}
    assert (await client.get("/one/openai/chat-disclaimer", headers={**headers, "lang": "fr"})).json() == "Prüfen."
    assert (await client.get("/one/openai/chat-disclaimer", headers={**headers, "lang": "en"})).json() == "Verify."
    assert (
        await client.get("/two/openai/chat-disclaimer", headers={**headers, "lang": "en"})
    ).json() == "AI can make mistakes. Please verify answers."
    await TenantMetadataEntity.update_tenant_metadata("one", chat_disclaimer=LocaleString(it="Verifica."))
    assert (await client.get("/one/openai/chat-disclaimer", headers={**headers, "lang": "en"})).json() == "Verifica."
