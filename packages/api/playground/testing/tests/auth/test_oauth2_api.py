from datetime import UTC, datetime, timedelta

import httpx
import jwt
import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from mongoengine import connect, disconnect
from swiss_ai_hub.core.auth import KeycloakSettings
from swiss_ai_hub.core.auth.dependencies.dangerous_development_only_auth_handler.dangerous_development_only_auth_settings import (  # noqa: E501
    DangerousDevelopmentOnlyAuthSettings,
)
from swiss_ai_hub.core.auth.dependencies.keycloak_auth_handler import KeycloakAuthHandler
from swiss_ai_hub.core.infrastructure import AIHubSettings, MongoSettings
from swiss_ai_hub.core.persistence.access.entities.tenant_entity import TenantEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity
from swiss_ai_hub.core.testing import (
    DummyResponse,
    generate_rsa_keypair,
    public_key_to_jwk,
)

from swiss_ai_hub.api.routes.my_account.my_account_controller import MyAccountController
from swiss_ai_hub.api.runners.api_test_runner import ApiTestRunner

# Constants for the tests
BASE_URL = "http://test"
USER_ENDPOINT = "/api/v1/active/my-account"
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
def keycloak_config(monkeypatch):
    """Set Keycloak env vars and return a KeycloakSettings instance."""
    return KeycloakSettings()


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
def monkeypatch_httpx(monkeypatch, fake_jwks_response, keycloak_config):
    """Monkeypatch httpx.AsyncClient.get to return a fake JWKS response only for JWKS URL."""

    original_get = httpx.AsyncClient.get

    async def patched_get(self, url, **kwargs):
        if url == keycloak_config.JWKS_URL or url.endswith("/protocol/openid-connect/certs"):
            return DummyResponse(fake_jwks_response, status_code=200)
        return await original_get(self, url, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "get", patched_get)


@pytest.fixture
def valid_keycloak_token(keycloak_config, rsa_keys):
    """Generate a valid Keycloak JWT token with test claims."""
    now = datetime.now(UTC)
    exp = now + timedelta(minutes=TOKEN_EXPIRY_MINUTES)
    payload = {
        "name": DangerousDevelopmentOnlyAuthSettings().NAME,
        "email": DangerousDevelopmentOnlyAuthSettings().EMAIL,
        "preferred_username": DangerousDevelopmentOnlyAuthSettings().EMAIL,
        "roles": DangerousDevelopmentOnlyAuthSettings().ROLES,
        "aud": "account",
        "sub": DangerousDevelopmentOnlyAuthSettings().OID,
        "iss": keycloak_config.ISSUER_URL,
        "exp": exp,
    }
    headers = {"kid": rsa_keys["kid"]}
    token = jwt.encode(payload, rsa_keys["private_key"], algorithm="RS256", headers=headers)
    return token


@pytest.fixture
def setup_test_user(mongo_db):
    """Create the test user with expected roles before the test runs."""
    config = DangerousDevelopmentOnlyAuthSettings()

    # Assign the expected roles in the default tenant
    default_tenant = TenantEntity.get_default_tenant()
    user_tenant_role = None
    if default_tenant:
        user_tenant_role = UserTenantRoleEntity.create_or_update(
            user_id=config.OID,
            tenant_id=str(default_tenant.id),
            roles=config.ROLES,
            validate_roles=False,
        )

    yield config

    # Cleanup
    if user_tenant_role:
        user_tenant_role.delete()


@pytest.fixture
def expected_user_data():
    """Return the expected user data from token claims."""
    return {
        "id": DangerousDevelopmentOnlyAuthSettings().OID,
        "name": DangerousDevelopmentOnlyAuthSettings().NAME,
        "email": DangerousDevelopmentOnlyAuthSettings().EMAIL,
        "profile_image": None,
        "roles": DangerousDevelopmentOnlyAuthSettings().ROLES,
    }


@pytest_asyncio.fixture(scope="module")
async def keycloak_api_client():
    """Return a TestClient with KeycloakAuthHandler and MyAccountController mounted."""
    runner = ApiTestRunner()
    auth = KeycloakAuthHandler()
    runner.mount(MyAccountController(auth=auth).get_my_account())
    app = runner.create_app()
    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url=BASE_URL) as client:
            yield client


@pytest.mark.asyncio
async def test_get_user_with_valid_keycloak_token(
    keycloak_api_client, valid_keycloak_token, expected_user_data, setup_test_user
):
    """Test GET /my-account returns expected user data with a valid Keycloak token."""
    headers = {
        "Authorization": f"Bearer {valid_keycloak_token}",
        "Content-Type": "application/json",
    }
    response = await keycloak_api_client.get(USER_ENDPOINT, headers=headers)
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.text}"
    user_data = response.json()

    # These fields are tested in other tests
    del user_data["dashboard"]
    del user_data["access"]

    assert all(key in user_data for key in EXPECTED_USER_FIELDS)
    assert user_data == expected_user_data


@pytest.mark.asyncio
async def test_get_user_with_invalid_keycloak_token(keycloak_api_client):
    """Test GET /my-account returns an error for an invalid Keycloak token."""
    headers = {
        "Authorization": "Bearer invalid.token.value",
        "Content-Type": "application/json",
    }
    response = await keycloak_api_client.get(USER_ENDPOINT, headers=headers)
    assert response.status_code in (
        401,
        403,
    ), f"Expected 401/403 for invalid token but got {response.status_code}: {response.text}"
