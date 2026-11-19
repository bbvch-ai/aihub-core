from datetime import UTC, datetime, timedelta

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient
from mongoengine import connect, disconnect
from swiss_ai_hub.core.infrastructure import AIHubSettings, MongoSettings
from swiss_ai_hub.core.persistence import BearerToken
from swiss_ai_hub.core.testing.auth_utils import TEST_USER_OID, TestAuthHandler

from swiss_ai_hub.api.routes.token.token_controller import TokenController
from swiss_ai_hub.api.runners.api_test_runner import ApiTestRunner

TOKEN_BASE = "/api/v1/active/tokens"
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
    auth = TestAuthHandler()
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
    response = api_client.delete(f"{TOKEN_BASE}/123456789012345678901234")
    assert response.status_code == 404


def test_revoke_malformed_token_id(api_client):
    response = api_client.delete(f"{TOKEN_BASE}/not-an-object-id")
    assert response.status_code == 404


def test_revoke_another_users_token(api_client):
    """Another user's token must look exactly like a missing one and stay valid."""
    foreign = BearerToken.create_new_token("foreign", datetime.now(UTC) + timedelta(days=1), str(ObjectId()))

    response = api_client.delete(f"{TOKEN_BASE}/{foreign.id}")

    assert response.status_code == 404
    assert BearerToken.objects(id=foreign.id).count() == 1


def test_static_token_is_neither_listed_nor_revocable(api_client):
    """The superuser token is seeded for the superuser account; that user must not be able to cut internal services
    off by revoking it."""
    static = BearerToken.upsert_static_token(
        name="superuser-static-token",
        token_value=f"sk-static-{ObjectId()}",
        expiry_date=datetime.now(UTC) + timedelta(days=1),
        user_oid=TEST_USER_OID,
    )

    listed_ids = [token["id"] for token in api_client.get(f"{TOKEN_BASE}/").json()]
    response = api_client.delete(f"{TOKEN_BASE}/{static.id}")

    assert str(static.id) not in listed_ids
    assert response.status_code == 404
    assert BearerToken.objects(id=static.id).count() == 1


def test_list_reports_creation_and_last_use(api_client, valid_token_request):
    created = api_client.post(f"{TOKEN_BASE}/", json=valid_token_request).json()

    unused = api_client.get(f"{TOKEN_BASE}/").json()[0]
    used_at = datetime.now(UTC)
    BearerToken.objects.get(id=created["id"]).record_use(used_at)
    used = api_client.get(f"{TOKEN_BASE}/").json()[0]

    assert unused["id"] == created["id"]
    assert unused["created_at"] is not None
    assert unused["last_used_at"] is None
    assert "roles" not in unused
    reported_use = datetime.fromisoformat(used["last_used_at"])
    assert reported_use.tzinfo is not None, "Without an offset a browser reads the time as local"
    assert abs(reported_use - used_at) < timedelta(seconds=1)
    assert datetime.fromisoformat(unused["expiry_date"]).tzinfo is not None


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
    assert any(expected_error in error for error in error_details), (
        f"Expected error '{expected_error}' not found in {error_details}"
    )
