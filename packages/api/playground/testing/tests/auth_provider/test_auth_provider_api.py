from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from swiss_ai_hub.core.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthHandler import (
    DangerousDevelopmentOnlyAuthHandler,
)
from swiss_ai_hub.core.testing.auth_utils.tenant_mocks import mock_tenant_entity_autouse  # noqa: F401
from swiss_ai_hub.core.testing.auth_utils.user_mocks import mock_user_entity_autouse  # noqa: F401

from swiss_ai_hub.api.routes.auth_provider.AuthProviderController import AuthProviderController
from swiss_ai_hub.api.routes.auth_provider.AuthProviderService import AuthProviderService
from swiss_ai_hub.api.routes.auth_provider.dto.AuthProviderResponse import AuthProviderResponse
from swiss_ai_hub.api.runners.ApiTestRunner import ApiTestRunner

BASE_ENDPOINT = "/api/v1/auth-providers"


@pytest.fixture
def api_client():
    auth = DangerousDevelopmentOnlyAuthHandler()
    runner = ApiTestRunner()
    runner.mount(AuthProviderController(auth=auth).get_auth_providers())
    app = runner.create_app()
    app.state.redis = AsyncMock()
    return TestClient(app)


def test_get_auth_providers_returns_list(api_client, monkeypatch):
    async def mock_get(redis):
        return [
            AuthProviderResponse(alias="azure-ad", display_name="Microsoft", icon="pi-microsoft"),
            AuthProviderResponse(alias="", display_name="Keycloak", icon="pi-lock"),
        ]

    monkeypatch.setattr(AuthProviderService, "get_auth_providers", mock_get)

    response = api_client.get(BASE_ENDPOINT + "/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["alias"] == "azure-ad"
    assert data[0]["display_name"] == "Microsoft"
    assert data[0]["icon"] == "pi-microsoft"
    assert data[1]["alias"] == ""
    assert data[1]["display_name"] == "Keycloak"


def test_get_auth_providers_empty(api_client, monkeypatch):
    async def mock_get(redis):
        return []

    monkeypatch.setattr(AuthProviderService, "get_auth_providers", mock_get)

    response = api_client.get(BASE_ENDPOINT + "/")
    assert response.status_code == 200
    assert response.json() == []


def test_get_auth_providers_unauthenticated(api_client, monkeypatch):
    async def mock_get(redis):
        return [AuthProviderResponse(alias="test", display_name="Test", icon="pi-lock")]

    monkeypatch.setattr(AuthProviderService, "get_auth_providers", mock_get)

    response = api_client.get(BASE_ENDPOINT + "/")
    assert response.status_code == 200
