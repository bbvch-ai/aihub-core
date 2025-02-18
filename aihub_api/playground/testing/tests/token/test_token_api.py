import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from mongoengine import connect, disconnect

from aihub_api.routes.token.TokenController import ApiTokenController
from aihub_api.runners.ApiTestRunner import ApiTestRunner
from aihub_lib.auth.dependencies.NoAuthHandler.NoAuthHandler import NoAuthHandler
from aihub_lib.infrastructure.ApiConfig import ApiConfig
from aihub_lib.infrastructure.azure.cosmos.CosmosAccess import CosmosAccess
from aihub_lib.persistence.access.entities.BearerToken import BearerToken


@pytest.fixture(scope="function")
def mongodb():
    """Setup a test MongoDB connection and clear data after each test."""
    yield
    connect(
        db=ApiConfig().DB_NAME,
        host=CosmosAccess().get_connection_string(),
        alias="default"
    )
    BearerToken.objects.delete()
    disconnect()


@pytest.fixture
def api_client(mongodb):
    """Create test client with ApiTokenController mounted."""
    runner = ApiTestRunner()
    auth = NoAuthHandler()
    runner.mount(
        ApiTokenController(auth=auth)
        .create_token()
        .list_tokens()
        .revoke_token()
    )
    with TestClient(runner.get_app(), raise_server_exceptions=True) as client:
        yield client


@pytest.fixture
def valid_token_request():
    """Create a valid token request payload."""
    expiry_date = datetime.now(timezone.utc) + timedelta(days=365)
    return {
        "name": "Test Token",
        "expiry_date": expiry_date.isoformat(),
        "roles": ["read", "write"]
    }


def test_create_token(api_client, valid_token_request):
    """Test creating a new API token."""
    # When
    response = api_client.post("/api/v1/tokens/", json=valid_token_request)

    # Then
    if response.status_code != 201:
        error_detail = response.json().get('detail', 'No error detail provided')
        pytest.fail(f"Expected status code 201, got {response.status_code}. Error: {error_detail}")

    data = response.json()
    assert "id" in data, f"Response missing 'id' field. Got: {data}"
    assert "token" in data, f"Response missing 'token' field. Got: {data}"
    assert data["name"] == valid_token_request["name"]
    assert all(role in data["roles"] for role in valid_token_request["roles"])


def test_create_token_with_past_date(api_client, valid_token_request):
    """Test creating a token with past expiry date."""
    # Given
    valid_token_request["expiry_date"] = (
            datetime.now(timezone.utc) - timedelta(days=1)
    ).isoformat()

    # When
    response = api_client.post("/api/v1/tokens/", json=valid_token_request)

    # Then
    assert response.status_code == 422  # Unprocessable Entity
    error_response = response.json()
    error_details = [error["msg"] for error in error_response["detail"]]
    assert any("Expiry date must be in the future" in error for error in error_details)



def test_list_tokens(api_client, valid_token_request):
    """Test listing API tokens."""
    # Given
    create_response = api_client.post("/api/v1/tokens/", json=valid_token_request)
    assert create_response.status_code == 201

    # When
    response = api_client.get("/api/v1/tokens/")

    # Then
    assert response.status_code == 200
    tokens = response.json()
    assert len(tokens) > 0
    assert "token" not in tokens[0]  # Token value should not be returned in list
    assert tokens[0]["name"] == valid_token_request["name"]


def test_revoke_token(api_client, valid_token_request):
    """Test revoking an API token."""
    # Given
    create_response = api_client.post("/api/v1/tokens/", json=valid_token_request)
    assert create_response.status_code == 201
    token_id = create_response.json()["id"]

    # When
    response = api_client.delete(f"/api/v1/tokens/{token_id}")

    # Then
    assert response.status_code == 200
    assert "revoked successfully" in response.json()["detail"]

    # Verify token is actually deleted
    list_response = api_client.get("/api/v1/tokens/")
    assert token_id not in [t["id"] for t in list_response.json()]


def test_revoke_nonexistent_token(api_client):
    """Test revoking a non-existent token."""
    # When
    response = api_client.delete("/api/v1/tokens/123456789012345678901234")

    # Then
    assert response.status_code == 400


@pytest.mark.parametrize("invalid_request,expected_error,expected_status", [
    (
            {
                "name": "",  # Empty name
                "expiry_date": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
                "roles": ["read"]
            },
            "String should have at least 1 character",
            422
    ),
    (
            {
                "name": "   ",  # Only whitespace
                "expiry_date": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
                "roles": ["read"]
            },
            "String should have at least 1 character",
            422
    ),
    (
            {
                "name": "x" * 101,  # Too long name
                "expiry_date": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
                "roles": ["read"]
            },
            "String should have at most 100 characters",
            422
    ),
    (
            {
                "name": "Test Token",
                "expiry_date": (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(),
                "roles": ["read"]
            },
            "Expiry date must be in the future",
            422
    ),
    (
            {
                "name": "Test Token",
                "expiry_date": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
                "roles": []  # Empty roles list
            },
            "List should have at least 1 item",
            422
    ),
    (
            {
                "name": "Test Token",
                "expiry_date": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
                "roles": ["read", "read"]  # Duplicate roles
            },
            "Roles must be unique",
            422
    ),
    (
            {
                "name": "Test Token",
                "expiry_date": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
                "roles": [""]  # Empty role string
            },
            "String should have at least 1 character",
            422
    ),
    (
            {
                "name": "Test Token",
                "expiry_date": "invalid-date",
                "roles": ["read"]
            },
            "Input should be a valid datetime",  # Updated error message
            422
    )
])
def test_create_token_validation(api_client, invalid_request, expected_error, expected_status):
    """Test token creation with invalid requests."""
    response = api_client.post("/api/v1/tokens/", json=invalid_request)
    assert response.status_code == expected_status

    error_response = response.json()
    error_details = [error["msg"] for error in error_response["detail"]]
    assert any(expected_error in error for error in error_details), \
        f"Expected error '{expected_error}' not found in {error_details}"