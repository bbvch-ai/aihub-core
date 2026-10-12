from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from swiss_ai_hub.core.testing.auth_utils import TestAuthHandler

from swiss_ai_hub.api.routes.auth_provider.auth_provider_controller import AuthProviderController
from swiss_ai_hub.api.routes.auth_provider.auth_provider_service import AuthProviderService
from swiss_ai_hub.api.routes.auth_provider.dto.auth_provider_response import AuthProviderResponse
from swiss_ai_hub.api.routes.auth_provider.dto.login_options_response import LoginOptionsResponse
from swiss_ai_hub.api.runners.api_test_runner import ApiTestRunner

BASE_ENDPOINT = "/api/v1/auth-providers"


@pytest.fixture
def api_client():
    auth = TestAuthHandler()
    runner = ApiTestRunner()
    runner.mount(AuthProviderController(auth=auth).get_auth_providers().get_auth_provider())
    app = runner.create_app()
    app.state.redis = AsyncMock()
    return TestClient(app)


def test_get_auth_providers_returns_list(api_client, monkeypatch):
    async def mock_get(redis):
        return LoginOptionsResponse(
            welcome_page=False,
            providers=[
                AuthProviderResponse(alias="azure-ad", display_name="Microsoft", icon="pi-microsoft"),
                AuthProviderResponse(alias="", display_name="Keycloak", icon="pi-lock"),
            ],
        )

    monkeypatch.setattr(AuthProviderService, "get_login_options", mock_get)

    response = api_client.get(BASE_ENDPOINT + "/")
    assert response.status_code == 200
    data = response.json()
    assert data["welcome_page"] is False
    providers = data["providers"]
    assert len(providers) == 2
    assert providers[0]["alias"] == "azure-ad"
    assert providers[0]["display_name"] == "Microsoft"
    assert providers[0]["icon"] == "pi-microsoft"
    assert providers[1]["alias"] == ""
    assert providers[1]["display_name"] == "Keycloak"


def test_get_auth_providers_empty(api_client, monkeypatch):
    async def mock_get(redis):
        return LoginOptionsResponse(welcome_page=False, providers=[])

    monkeypatch.setattr(AuthProviderService, "get_login_options", mock_get)

    response = api_client.get(BASE_ENDPOINT + "/")
    assert response.status_code == 200
    assert response.json() == {"welcome_page": False, "providers": []}


def test_get_auth_providers_welcome_page(api_client, monkeypatch):
    async def mock_get(redis):
        return LoginOptionsResponse(
            welcome_page=True, providers=[AuthProviderResponse(alias="", display_name="Keycloak", icon="pi-lock")]
        )

    monkeypatch.setattr(AuthProviderService, "get_login_options", mock_get)

    response = api_client.get(BASE_ENDPOINT + "/")
    assert response.status_code == 200
    assert response.json() == {
        "welcome_page": True,
        "providers": [{"alias": "", "display_name": "Keycloak", "icon": "pi-lock"}],
    }


def test_get_auth_providers_unauthenticated(api_client, monkeypatch):
    async def mock_get(redis):
        return LoginOptionsResponse(
            welcome_page=False, providers=[AuthProviderResponse(alias="test", display_name="Test", icon="pi-lock")]
        )

    monkeypatch.setattr(AuthProviderService, "get_login_options", mock_get)

    response = api_client.get(BASE_ENDPOINT + "/")
    assert response.status_code == 200


def test_get_auth_provider_returns_matching_provider(api_client, monkeypatch):
    async def mock_get(redis, alias):
        return AuthProviderResponse(alias=alias, display_name="Acme", icon="pi-microsoft")

    monkeypatch.setattr(AuthProviderService, "get_auth_provider", mock_get)

    response = api_client.get(BASE_ENDPOINT + "/acme-entra")
    assert response.status_code == 200
    assert response.json() == {"alias": "acme-entra", "display_name": "Acme", "icon": "pi-microsoft"}


def test_get_auth_provider_unknown_alias_returns_null(api_client, monkeypatch):
    async def mock_get(redis, alias):
        return None

    monkeypatch.setattr(AuthProviderService, "get_auth_provider", mock_get)

    response = api_client.get(BASE_ENDPOINT + "/unknown")
    assert response.status_code == 200
    assert response.json() is None
