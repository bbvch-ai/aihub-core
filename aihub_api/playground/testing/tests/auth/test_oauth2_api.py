from datetime import datetime, timedelta, timezone

import pytest
import jwt
import httpx
from fastapi.testclient import TestClient
from mongoengine import connect, disconnect

from aihub_api.runners.ApiTestRunner import ApiTestRunner
from aihub_api.routes.user.UserController import UserController
from aihub_lib.auth.dependencies.OAuth2AuthHandler.OAuth2AuthHandler import OAuth2AuthHandler
from aihub_lib.auth.dependencies.OAuth2AuthHandler.OAuth2Config import OAuth2Config
from aihub_lib.auth.identity.AzureIdentityProvider.AzureIdentityProvider import AzureIdentityProvider
from aihub_lib.infrastructure.ApiConfig import ApiConfig
from aihub_lib.infrastructure.azure.cosmos.CosmosAccess import CosmosAccess
from aihub_lib.testing.auth_utils.oauth2_utils.oauth2_test_utils import (
    generate_rsa_keypair,
    public_key_to_jwk,
    DummyResponse,
)

# Constants for the tests
USER_ENDPOINT = "/api/v1/users/me"
EXPECTED_USER_FIELDS = ["id", "name", "email"]
TOKEN_EXPIRY_MINUTES = 10


@pytest.fixture(scope="module", autouse=True)
def mongo_db():
    """Set up and tear down the MongoDB connection for tests."""
    connect(db=ApiConfig().DB_NAME, host=CosmosAccess().get_connection_string())
    yield
    disconnect()


@pytest.fixture(autouse=True)
def oauth2_config(monkeypatch):
    """Set OAuth2 env vars and return an OAuth2Config instance."""
    return OAuth2Config()


@pytest.fixture
def rsa_keys():
    """Generate RSA key pair and return keys and JWK with a fixed kid."""
    private_key, public_key = generate_rsa_keypair()
    kid = "test-key-id"
    jwk = public_key_to_jwk(public_key, kid)
    return {"private_key": private_key, "public_key": public_key, "kid": kid, "jwk": jwk}


@pytest.fixture
def fake_jwks_response(rsa_keys):
    """Return a fake JWKS response containing the generated public key."""
    return {"keys": [rsa_keys["jwk"]]}


@pytest.fixture(autouse=True)
def monkeypatch_httpx(monkeypatch, fake_jwks_response, oauth2_config):
    """Monkeypatch httpx.AsyncClient.get to return a fake JWKS response."""

    async def fake_get(self, url, **kwargs):
        return DummyResponse(fake_jwks_response, status_code=200)

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)


@pytest.fixture
def valid_oauth2_token(oauth2_config, rsa_keys):
    """Generate a valid OAuth2 JWT token with test claims."""
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=TOKEN_EXPIRY_MINUTES)
    payload = {
        "name": "Melanie Musterfrau",
        "preferred_username": "melanie.musterfrau@bbv.ch",
        "roles": ["user"],
        "aud": oauth2_config.CLIENT_ID,
        "oid": "1234567890",
        "iss": f"{oauth2_config.AUTHORITY}/v2.0",
        "exp": exp,
    }
    headers = {"kid": rsa_keys["kid"]}
    token = jwt.encode(payload, rsa_keys["private_key"], algorithm="RS256", headers=headers)
    return token


@pytest.fixture
def expected_user_data():
    """Return the expected user data from token claims."""
    return {
        "id": "1234567890",
        "name": "Melanie Musterfrau",
        "email": "melanie.musterfrau@bbv.ch",
        "profile_image": None,
        "roles": ["AllAgents"],
        "favorite_modules": [],
    }


@pytest.fixture
def oauth2_api_client():
    """Return a TestClient with OAuth2AuthHandler and UserController mounted."""
    runner = ApiTestRunner()
    auth = OAuth2AuthHandler(identity_provider=AzureIdentityProvider())
    runner.mount(UserController(auth=auth).get_my_user())
    return TestClient(runner.get_app())


def test_get_user_with_valid_oauth2_token(oauth2_api_client, valid_oauth2_token, expected_user_data):
    """Test GET /user/me returns expected user data with a valid OAuth2 token."""
    headers = {
        "Authorization": f"Bearer {valid_oauth2_token}",
        "Content-Type": "application/json",
    }
    response = oauth2_api_client.get(USER_ENDPOINT, headers=headers)
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.text}"
    user_data = response.json()
    del user_data["dashboard"]
    assert all(key in user_data for key in EXPECTED_USER_FIELDS)
    assert user_data == expected_user_data


def test_get_user_with_invalid_oauth2_token(oauth2_api_client):
    """Test GET /user/me returns an error for an invalid OAuth2 token."""
    headers = {
        "Authorization": "Bearer invalid.token.value",
        "Content-Type": "application/json",
    }
    response = oauth2_api_client.get(USER_ENDPOINT, headers=headers)
    assert response.status_code in (
        401,
        403,
    ), f"Expected 401/403 for invalid token but got {response.status_code}: {response.text}"
