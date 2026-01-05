from datetime import UTC, datetime, timedelta

import pytest
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthHandler import (
    DangerousDevelopmentOnlyAuthHandler,
)
from aihub_lib.auth.identity.DangerousDevelopmentOnlyIdentityProvider.DangerousDevelopmentOnlyIdentityProvider import (
    DangerousDevelopmentOnlyIdentityProvider,
)
from aihub_lib.infrastructure.api.AIHubSettings import AIHubSettings
from aihub_lib.infrastructure.mongo.MongoSettings import MongoSettings
from aihub_lib.persistence.access.entities.BearerToken import BearerToken
from aihub_lib.testing.auth_utils.role_mocks import mock_role_entity_admin_only  # noqa: F401
from fastapi.testclient import TestClient
from mongoengine import connect, disconnect

from aihub_api.routes.token.TokenController import TokenController
from aihub_api.runners.ApiTestRunner import ApiTestRunner

TOKEN_BASE = "/api/v1/tokens"
DEFAULT_USER_ID = "1234567890"


@pytest.fixture(scope="function")
def mongodb():
    """Setup a test MongoDB connection and clear data after each test."""
    yield
    connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
        uuidRepresentation="standard",
    )
    BearerToken.objects.delete()
    disconnect()


@pytest.fixture
def api_client(mongodb):
    """Create test client with ApiTokenController mounted."""
    runner = ApiTestRunner()
    auth = DangerousDevelopmentOnlyAuthHandler(identity_provider=DangerousDevelopmentOnlyIdentityProvider())
    runner.mount(TokenController(auth=auth).create_token().list_tokens().revoke_token())
    with TestClient(runner.create_app(), raise_server_exceptions=True) as client:
        yield client


@pytest.fixture
def valid_token_request():
    """Return a valid token request payload."""
    expiry_date = datetime.now(UTC) + timedelta(days=365)
    return {"name": "Test Token", "expiry_date": expiry_date.isoformat()}


def test_create_token(api_client, valid_token_request):
    """Test creating a new API token returns valid data."""
    response = api_client.post(f"{TOKEN_BASE}/", json=valid_token_request)
    if response.status_code != 201:
        error_detail = response.json().get("detail", "No error detail provided")
        pytest.fail(f"Expected status code 201, got {response.status_code}. Error: {error_detail}")
    data = response.json()
    assert "id" in data, f"Response missing 'id'. Got: {data}"
    assert "token" in data, f"Response missing 'token'. Got: {data}"
    assert data["name"] == valid_token_request["name"]


def test_create_token_with_past_date(api_client, valid_token_request):
    """Test creating a token with past expiry date returns validation error."""
    valid_token_request["expiry_date"] = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    response = api_client.post(f"{TOKEN_BASE}/", json=valid_token_request)
    assert response.status_code == 422
    error_response = response.json()
    error_details = [error["msg"] for error in error_response["detail"]]
    assert any("Expiry date must be in the future" in error for error in error_details)


def test_list_tokens(api_client, valid_token_request):
    """Test listing API tokens returns created token without token value."""
    create_response = api_client.post(f"{TOKEN_BASE}/", json=valid_token_request)
    assert create_response.status_code == 201
    response = api_client.get(f"{TOKEN_BASE}/")
    assert response.status_code == 200
    tokens = response.json()
    assert len(tokens) > 0
    assert "token" not in tokens[0]
    assert tokens[0]["name"] == valid_token_request["name"]


def test_revoke_token(api_client, valid_token_request):
    """Test revoking an API token removes it from the list."""
    create_response = api_client.post(f"{TOKEN_BASE}/", json=valid_token_request)
    assert create_response.status_code == 201
    token_id = create_response.json()["id"]
    response = api_client.delete(f"{TOKEN_BASE}/{token_id}")
    assert response.status_code == 200
    assert "revoked successfully" in response.json()["detail"]
    list_response = api_client.get(f"{TOKEN_BASE}/")
    token_ids = [t["id"] for t in list_response.json()]
    assert token_id not in token_ids


def test_revoke_nonexistent_token(api_client):
    """Test revoking a non-existent token returns error."""
    response = api_client.delete(f"{TOKEN_BASE}/123456789012345678901234")
    assert response.status_code == 400


@pytest.mark.parametrize(
    "invalid_request,expected_error,expected_status",
    [
        (
            {
                "name": "",
                "expiry_date": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
            },
            "String should have at least 1 character",
            422,
        ),
        (
            {
                "name": "   ",
                "expiry_date": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
            },
            "String should have at least 1 character",
            422,
        ),
        (
            {
                "name": "x" * 101,
                "expiry_date": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
            },
            "String should have at most 100 characters",
            422,
        ),
        (
            {
                "name": "Test Token",
                "expiry_date": (datetime.now(UTC) - timedelta(seconds=1)).isoformat(),
            },
            "Expiry date must be in the future",
            422,
        ),
        (
            {"name": "Test Token", "expiry_date": "invalid-date"},
            "Input should be a valid datetime",
            422,
        ),
    ],
)
def test_create_token_validation(
    api_client,
    invalid_request,
    expected_error,
    expected_status,
):
    """Test token creation with invalid payload returns proper validation errors."""
    response = api_client.post(f"{TOKEN_BASE}/", json=invalid_request)
    assert response.status_code == expected_status
    error_response = response.json()
    error_details = [error["msg"] for error in error_response["detail"]]
    assert any(
        expected_error in error for error in error_details
    ), f"Expected error '{expected_error}' not found in {error_details}"
