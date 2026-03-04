from unittest.mock import AsyncMock, patch

import pytest

from aihub_api.routes.auth_provider.AuthProviderService import (
    CACHE_KEY,
    DEFAULT_ICON,
    AuthProviderService,
)


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.get.return_value = None
    return redis


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


def test_filters_disabled_providers():
    idps = [
        _build_idp(alias="active", enabled=True),
        _build_idp(alias="disabled", enabled=False),
    ]

    providers = AuthProviderService._filter_providers(idps)

    aliases = [p.alias for p in providers]
    assert "active" in aliases
    assert "disabled" not in aliases


def test_filters_hidden_providers():
    idps = [
        _build_idp(alias="visible"),
        _build_idp(alias="hidden", hide_on_login=True),
    ]

    providers = AuthProviderService._filter_providers(idps)

    aliases = [p.alias for p in providers]
    assert "visible" in aliases
    assert "hidden" not in aliases


def test_filters_link_only_providers():
    idps = [
        _build_idp(alias="normal"),
        _build_idp(alias="link-only", link_only=True),
    ]

    providers = AuthProviderService._filter_providers(idps)

    aliases = [p.alias for p in providers]
    assert "normal" in aliases
    assert "link-only" not in aliases


def test_icon_from_keycloak_config():
    idps = [_build_idp(alias="azure-ad", icon="pi-microsoft")]

    providers = AuthProviderService._filter_providers(idps)

    assert providers[0].icon == "pi-microsoft"


def test_icon_falls_back_to_default_when_not_configured():
    idps = [_build_idp(alias="custom-idp")]

    providers = AuthProviderService._filter_providers(idps)

    assert providers[0].icon == DEFAULT_ICON


@pytest.mark.asyncio
async def test_returns_cached_result_from_redis(mock_redis):
    import json

    cached_data = [{"alias": "cached", "display_name": "Cached IDP", "icon": "pi-lock"}]
    mock_redis.get.return_value = json.dumps(cached_data)

    providers = await AuthProviderService.get_auth_providers(mock_redis)

    assert len(providers) == 1
    assert providers[0].alias == "cached"
    mock_redis.get.assert_called_once_with(CACHE_KEY)


@pytest.mark.asyncio
async def test_stores_result_in_redis(mock_redis):
    mock_admin = AsyncMock()
    mock_admin.a_get_idps.return_value = [_build_idp(alias="azure-ad")]

    with (
        patch("aihub_api.routes.auth_provider.AuthProviderService.KeycloakAdmin", return_value=mock_admin),
        patch(
            "aihub_api.routes.auth_provider.AuthProviderService.KeycloakSettings",
            return_value=type("S", (), {"URL": "http://kc:8080", "REALM": "aihub", "API_SERVICE_CLIENT_ID": "svc", "API_SERVICE_CLIENT_SECRET": "secret", "SHOW_KEYCLOAK_LOGIN": False})(),
        ),
    ):
        await AuthProviderService.get_auth_providers(mock_redis)

    mock_redis.set.assert_called_once()
    call_args = mock_redis.set.call_args
    assert call_args[0][0] == CACHE_KEY


@pytest.mark.asyncio
async def test_appends_keycloak_login_when_show_login_true(mock_redis):
    mock_admin = AsyncMock()
    mock_admin.a_get_idps.return_value = []

    with (
        patch("aihub_api.routes.auth_provider.AuthProviderService.KeycloakAdmin", return_value=mock_admin),
        patch(
            "aihub_api.routes.auth_provider.AuthProviderService.KeycloakSettings",
            return_value=type("S", (), {"URL": "http://kc:8080", "REALM": "aihub", "API_SERVICE_CLIENT_ID": "svc", "API_SERVICE_CLIENT_SECRET": "secret", "SHOW_KEYCLOAK_LOGIN": True})(),
        ),
    ):
        providers = await AuthProviderService.get_auth_providers(mock_redis)

    assert len(providers) == 1
    assert providers[0].alias == ""
    assert providers[0].display_name == "Keycloak"
    assert providers[0].icon == "pi-lock"


@pytest.mark.asyncio
async def test_does_not_append_keycloak_login_when_show_login_false(mock_redis):
    mock_admin = AsyncMock()
    mock_admin.a_get_idps.return_value = []

    with (
        patch("aihub_api.routes.auth_provider.AuthProviderService.KeycloakAdmin", return_value=mock_admin),
        patch(
            "aihub_api.routes.auth_provider.AuthProviderService.KeycloakSettings",
            return_value=type("S", (), {"URL": "http://kc:8080", "REALM": "aihub", "API_SERVICE_CLIENT_ID": "svc", "API_SERVICE_CLIENT_SECRET": "secret", "SHOW_KEYCLOAK_LOGIN": False})(),
        ),
    ):
        providers = await AuthProviderService.get_auth_providers(mock_redis)

    assert providers == []


@pytest.mark.asyncio
async def test_propagates_keycloak_error(mock_redis):
    mock_admin = AsyncMock()
    mock_admin.a_get_idps.side_effect = Exception("connection refused")

    with (
        patch("aihub_api.routes.auth_provider.AuthProviderService.KeycloakAdmin", return_value=mock_admin),
        patch(
            "aihub_api.routes.auth_provider.AuthProviderService.KeycloakSettings",
            return_value=type("S", (), {"URL": "http://kc:8080", "REALM": "aihub", "API_SERVICE_CLIENT_ID": "svc", "API_SERVICE_CLIENT_SECRET": "secret", "SHOW_KEYCLOAK_LOGIN": False})(),
        ),
        pytest.raises(Exception, match="connection refused"),
    ):
        await AuthProviderService.get_auth_providers(mock_redis)


def test_display_name_falls_back_to_alias():
    idp = _build_idp(alias="my-idp", display_name="")
    idp["displayName"] = ""

    providers = AuthProviderService._filter_providers([idp])
    assert providers[0].display_name == "my-idp"
