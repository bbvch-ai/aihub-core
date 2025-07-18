import os
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from aihub_lib.auth.dependencies.TokenAuthHandler.TokenAuthHandler import TokenAuthHandler
from aihub_lib.auth.identity.TokenIdentityProvider.TokenIdentityProvider import TokenIdentityProvider
from aihub_lib.infrastructure.ApiConfig import ApiConfig
from aihub_lib.infrastructure.azure.cosmos.CosmosAccess import CosmosAccess
from aihub_lib.persistence.access.entities.BearerToken import BearerToken
from aihub_lib.persistence.user.UserEntity import UserEntity
from aihub_lib.testing.auth_utils.role_mocks import mock_role_entity_methods  # noqa: F401
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from mongoengine import connect, disconnect

from aihub_api.routes.user.UserController import UserController
from aihub_api.runners.ApiTestRunner import ApiTestRunner

BASE_URL = "http://test"
USER_ENDPOINT = "/api/v1/users/me"
EXPECTED_USER_FIELDS = ["id", "name", "email"]


@pytest.fixture(scope="module", autouse=True)
def mongo_db():
    """Set up and tear down the MongoDB connection for tests."""
    connect(db=ApiConfig().DB_NAME, host=CosmosAccess().get_connection_string())
    yield
    disconnect()


@pytest.fixture
def valid_token(mongo_db):
    """Insert a valid token document and return its token string."""
    user = UserEntity.create_user(
        oid=os.getenv("OID", "1234567890"),
        name=os.getenv("NAME", "Melanie Musterfrau"),
        email=os.getenv("EMAIL", "melanie.musterfrau@bbv.ch"),
        roles=["TestOnlyFullAdminAccess"],
    )
    expiry = datetime.now(UTC) + timedelta(hours=1)
    token_obj = BearerToken.create_new_token(name="token-name", expiry_date=expiry, user_oid=user.id)
    yield token_obj.token
    user.delete()
    token_obj.delete()


@pytest.fixture
def expected_user_data():
    """Return the expected user data based on environment variables."""
    return {
        "id": os.getenv("OID", "1234567890"),
        "name": os.getenv("NAME", "Melanie Musterfrau"),
        "email": os.getenv("EMAIL", "melanie.musterfrau@bbv.ch"),
        "profile_image": None,
        "roles": ["TestOnlyFullAdminAccess"],
        "favorite_modules": [],
    }


@pytest_asyncio.fixture(scope="module")
async def token_api_client():
    """Create a TestClient with UserController mounted using TokenAuthHandler."""
    runner = ApiTestRunner()
    auth = TokenAuthHandler(identity_provider=TokenIdentityProvider())
    runner.mount(UserController(auth=auth).get_my_user())
    app = runner.get_app()
    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url=BASE_URL) as client:
            yield client


@pytest.mark.asyncio
async def test_get_user_with_valid_token(token_api_client, valid_token, expected_user_data):
    """Test GET /user/me with a valid token returns expected user data."""
    headers = {
        "Authorization": f"Bearer {valid_token}",
        "Content-Type": "application/json",
    }
    response = await token_api_client.get(USER_ENDPOINT, headers=headers)
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.text}"
    user_data = response.json()

    # These fields are tested in other tests
    del user_data["dashboard"]
    del user_data["access"]
    del user_data["last_accessed"]

    assert all(key in user_data for key in EXPECTED_USER_FIELDS)
    assert user_data == expected_user_data


@pytest.mark.asyncio
async def test_get_user_with_invalid_token(token_api_client):
    """Test GET /user/me with an invalid token returns 401 or 403."""
    headers = {
        "Authorization": "Bearer invalid.token.value",
        "Content-Type": "application/json",
    }
    response = await token_api_client.get(USER_ENDPOINT, headers=headers)
    assert response.status_code in (
        401,
        403,
    ), f"Expected 401/403 for invalid token but got {response.status_code}: {response.text}"
