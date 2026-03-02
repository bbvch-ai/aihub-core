from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from aihub_api.routes.auth_provider.AuthProviderService import (
    DEFAULT_ICON,
    AuthProviderService,
)


def _mock_httpx_response(json_data: list[dict]) -> MagicMock:
    """Creates a mock httpx.Response with synchronous json()."""
    mock = MagicMock()
    mock.json.return_value = json_data
    mock.raise_for_status.return_value = None
    return mock


@pytest.fixture(autouse=True)
def _clear_cache():
    AuthProviderService._cache.clear()
    yield
    AuthProviderService._cache.clear()


def _mock_keycloak_settings(**overrides):
    defaults = {
        "URL": "http://keycloak:8080",
        "REALM": "aihub",
        "API_SERVICE_CLIENT_ID": "aihub-api-service",
        "API_SERVICE_CLIENT_SECRET": "test-secret",
        "SHOW_KEYCLOAK_LOGIN": True,
        "TOKEN_URL": "http://keycloak:8080/realms/aihub/protocol/openid-connect/token",
        "IDENTITY_PROVIDER_URL": "http://keycloak:8080/admin/realms/aihub/identity-provider/instances",
    }
    defaults.update(overrides)

    mock = type("MockSettings", (), defaults)()
    return mock


def _build_idp(
    alias: str = "azure-ad",
    display_name: str = "Microsoft",
    provider_id: str = "oidc",
    enabled: bool = True,
    hide_on_login: bool = False,
    link_only: bool = False,
    icon: str | None = None,
) -> dict:
    config = {}
    if hide_on_login:
        config["hideOnLoginPage"] = "true"
    if icon:
        config["icon"] = icon
    return {
        "alias": alias,
        "displayName": display_name,
        "providerId": provider_id,
        "enabled": enabled,
        "linkOnly": link_only,
        "config": config,
    }


@pytest.mark.asyncio
async def test_filters_disabled_providers():
    settings = _mock_keycloak_settings()
    idps = [
        _build_idp(alias="active", enabled=True),
        _build_idp(alias="disabled", enabled=False),
    ]

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = _mock_httpx_response(idps)
        providers = await AuthProviderService._fetch_identity_providers(settings, "token")

    aliases = [p.alias for p in providers]
    assert "active" in aliases
    assert "disabled" not in aliases


@pytest.mark.asyncio
async def test_filters_hidden_providers():
    settings = _mock_keycloak_settings()
    idps = [
        _build_idp(alias="visible"),
        _build_idp(alias="hidden", hide_on_login=True),
    ]

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = _mock_httpx_response(idps)
        providers = await AuthProviderService._fetch_identity_providers(settings, "token")

    aliases = [p.alias for p in providers]
    assert "visible" in aliases
    assert "hidden" not in aliases


@pytest.mark.asyncio
async def test_filters_link_only_providers():
    settings = _mock_keycloak_settings()
    idps = [
        _build_idp(alias="normal"),
        _build_idp(alias="link-only", link_only=True),
    ]

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = _mock_httpx_response(idps)
        providers = await AuthProviderService._fetch_identity_providers(settings, "token")

    aliases = [p.alias for p in providers]
    assert "normal" in aliases
    assert "link-only" not in aliases


@pytest.mark.asyncio
async def test_icon_from_keycloak_config():
    settings = _mock_keycloak_settings()
    idps = [_build_idp(alias="azure-ad", icon="pi-microsoft")]

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = _mock_httpx_response(idps)
        providers = await AuthProviderService._fetch_identity_providers(settings, "token")

    assert providers[0].icon == "pi-microsoft"


@pytest.mark.asyncio
async def test_icon_falls_back_to_default_when_not_configured():
    settings = _mock_keycloak_settings()
    idps = [_build_idp(alias="custom-idp")]

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = _mock_httpx_response(idps)
        providers = await AuthProviderService._fetch_identity_providers(settings, "token")

    assert providers[0].icon == DEFAULT_ICON


@pytest.mark.asyncio
async def test_returns_empty_when_no_secret_configured():
    settings = _mock_keycloak_settings(API_SERVICE_CLIENT_SECRET=None, SHOW_KEYCLOAK_LOGIN=False)

    with patch("aihub_api.routes.auth_provider.AuthProviderService.KeycloakSettings", return_value=settings):
        providers = await AuthProviderService.get_auth_providers()

    assert providers == []


@pytest.mark.asyncio
async def test_returns_keycloak_fallback_when_no_secret_and_show_login_true():
    settings = _mock_keycloak_settings(API_SERVICE_CLIENT_SECRET=None, SHOW_KEYCLOAK_LOGIN=True)

    with patch("aihub_api.routes.auth_provider.AuthProviderService.KeycloakSettings", return_value=settings):
        providers = await AuthProviderService.get_auth_providers()

    assert len(providers) == 1
    assert providers[0].alias == ""
    assert providers[0].display_name == "Keycloak"


@pytest.mark.asyncio
async def test_appends_keycloak_login_when_show_login_true():
    settings = _mock_keycloak_settings(SHOW_KEYCLOAK_LOGIN=True)

    with (
        patch.object(AuthProviderService, "_get_service_account_token", new_callable=AsyncMock, return_value="token"),
        patch.object(
            AuthProviderService,
            "_fetch_identity_providers",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch("aihub_api.routes.auth_provider.AuthProviderService.KeycloakSettings", return_value=settings),
    ):
        providers = await AuthProviderService.get_auth_providers()

    assert len(providers) == 1
    assert providers[0].alias == ""
    assert providers[0].display_name == "Keycloak"
    assert providers[0].icon == "pi-lock"


@pytest.mark.asyncio
async def test_does_not_append_keycloak_login_when_show_login_false():
    settings = _mock_keycloak_settings(SHOW_KEYCLOAK_LOGIN=False)

    with (
        patch.object(AuthProviderService, "_get_service_account_token", new_callable=AsyncMock, return_value="token"),
        patch.object(
            AuthProviderService,
            "_fetch_identity_providers",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch("aihub_api.routes.auth_provider.AuthProviderService.KeycloakSettings", return_value=settings),
    ):
        providers = await AuthProviderService.get_auth_providers()

    assert providers == []


@pytest.mark.asyncio
async def test_graceful_failure_on_http_error():
    settings = _mock_keycloak_settings(SHOW_KEYCLOAK_LOGIN=False)

    with (
        patch.object(
            AuthProviderService,
            "_get_service_account_token",
            new_callable=AsyncMock,
            side_effect=httpx.HTTPStatusError("error", request=None, response=None),
        ),
        patch("aihub_api.routes.auth_provider.AuthProviderService.KeycloakSettings", return_value=settings),
    ):
        providers = await AuthProviderService.get_auth_providers()

    assert providers == []


@pytest.mark.asyncio
async def test_caching_prevents_duplicate_calls():
    settings = _mock_keycloak_settings(SHOW_KEYCLOAK_LOGIN=False)
    mock_fetch = AsyncMock(return_value=[])
    mock_token = AsyncMock(return_value="token")

    with (
        patch.object(AuthProviderService, "_get_service_account_token", mock_token),
        patch.object(AuthProviderService, "_fetch_identity_providers", mock_fetch),
        patch("aihub_api.routes.auth_provider.AuthProviderService.KeycloakSettings", return_value=settings),
    ):
        await AuthProviderService.get_auth_providers()
        await AuthProviderService.get_auth_providers()

    mock_token.assert_called_once()
    mock_fetch.assert_called_once()


def test_display_name_falls_back_to_alias():
    idp = _build_idp(alias="my-idp", display_name="")
    idp["displayName"] = ""

    display_name = idp.get("displayName") or idp["alias"]
    assert display_name == "my-idp"
