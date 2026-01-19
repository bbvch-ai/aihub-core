from datetime import UTC, datetime, timedelta

import httpx
import jwt
import pytest
import pytest_asyncio
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from aihub_lib.auth.dependencies.OAuth2AuthHandler.OAuth2AuthHandler import OAuth2AuthHandler
from aihub_lib.auth.dependencies.OAuth2AuthHandler.OAuth2Settings import OAuth2Settings
from aihub_lib.auth.identity.DangerousDevelopmentOnlyIdentityProvider.DangerousDevelopmentOnlyIdentityProvider import (
    DangerousDevelopmentOnlyIdentityProvider,
)
from aihub_lib.infrastructure.api.AIHubSettings import AIHubSettings
from aihub_lib.infrastructure.mongo.MongoSettings import MongoSettings
from aihub_lib.testing.auth_utils.oauth2_utils.oauth2_test_utils import (
    DummyResponse,
    generate_rsa_keypair,
    public_key_to_jwk,
)
from aihub_lib.testing.auth_utils.role_mocks import mock_role_entity_methods  # noqa: F401
from aihub_lib.testing.auth_utils.user_mocks import mock_user_entity_autouse  # noqa: F401
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from mongoengine import connect, disconnect

from aihub_api.routes.my_account.MyAccountController import MyAccountController
from aihub_api.runners.ApiTestRunner import ApiTestRunner

# Constants for the tests
BASE_URL = "http://test"
USER_ENDPOINT = "/api/v1/my-account/"
EXPECTED_USER_FIELDS = ["id", "name", "email"]
TOKEN_EXPIRY_MINUTES = 10


@pytest.fixture(scope="module", autouse=True)
def mongo_db():
    """Set up and tear down the MongoDB connection for tests."""
    connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
        uuidRepresentation="standard",
    )
    yield
    disconnect()


@pytest.fixture(autouse=True)
def oauth2_config(monkeypatch):
    """Set OAuth2 env vars and return an OAuth2Settings instance."""
    return OAuth2Settings()


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
    """Monkeypatch httpx.AsyncClient.get to return a fake JWKS response only for JWKS URL."""

    original_get = httpx.AsyncClient.get

    async def patched_get(self, url, **kwargs):
        # Only mock requests to the JWKS URL
        if url == oauth2_config.JWKS_URL or url.endswith("/discovery/v2.0/keys"):
            return DummyResponse(fake_jwks_response, status_code=200)
        # For all other URLs, use the original method
        return await original_get(self, url, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "get", patched_get)


@pytest.fixture
def valid_oauth2_token(oauth2_config, rsa_keys):
    """Generate a valid OAuth2 JWT token with test claims."""
    now = datetime.now(UTC)
    exp = now + timedelta(minutes=TOKEN_EXPIRY_MINUTES)
    payload = {
        "name": DangerousDevelopmentOnlyAuthSettings().NAME,
        "preferred_username": DangerousDevelopmentOnlyAuthSettings().EMAIL,
        "roles": DangerousDevelopmentOnlyAuthSettings().ROLES,
        "aud": oauth2_config.CLIENT_ID,
        "oid": DangerousDevelopmentOnlyAuthSettings().OID,
        "iss": f"{oauth2_config.AUTHORITY_URL}/v2.0",
        "exp": exp,
    }
    headers = {"kid": rsa_keys["kid"]}
    token = jwt.encode(payload, rsa_keys["private_key"], algorithm="RS256", headers=headers)
    return token


@pytest.fixture
def expected_user_data():
    """Return the expected user data from token claims."""
    return {
        "id": DangerousDevelopmentOnlyAuthSettings().OID,
        "name": DangerousDevelopmentOnlyAuthSettings().NAME,
        "email": DangerousDevelopmentOnlyAuthSettings().EMAIL,
        "profile_image": None,
        "roles": DangerousDevelopmentOnlyAuthSettings().ROLES,
        "favorite_modules": [],
    }


@pytest_asyncio.fixture(scope="module")
async def oauth2_api_client():
    """Return a TestClient with OAuth2AuthHandler and MyAccountController mounted."""
    runner = ApiTestRunner()
    auth = OAuth2AuthHandler(identity_provider=DangerousDevelopmentOnlyIdentityProvider())
    runner.mount(MyAccountController(auth=auth).get_my_account())
    app = runner.create_app()
    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url=BASE_URL) as client:
            yield client


@pytest.mark.asyncio
async def test_get_user_with_valid_oauth2_token(oauth2_api_client, valid_oauth2_token, expected_user_data):
    """Test GET /user/me returns expected user data with a valid OAuth2 token."""
    headers = {
        "Authorization": f"Bearer {valid_oauth2_token}",
        "Content-Type": "application/json",
    }
    response = await oauth2_api_client.get(USER_ENDPOINT, headers=headers)
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.text}"
    user_data = response.json()

    # These fields are tested in other tests
    print("user_data", user_data)
    del user_data["dashboard"]
    del user_data["access"]
    del user_data["last_accessed"]

    assert all(key in user_data for key in EXPECTED_USER_FIELDS)
    assert user_data == expected_user_data


@pytest.mark.asyncio
async def test_get_user_with_invalid_oauth2_token(oauth2_api_client):
    """Test GET /user/me returns an error for an invalid OAuth2 token."""
    headers = {
        "Authorization": "Bearer invalid.token.value",
        "Content-Type": "application/json",
    }
    response = await oauth2_api_client.get(USER_ENDPOINT, headers=headers)
    assert response.status_code in (
        401,
        403,
    ), f"Expected 401/403 for invalid token but got {response.status_code}: {response.text}"
