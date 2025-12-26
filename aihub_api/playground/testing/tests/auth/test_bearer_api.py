import os
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from aihub_lib.auth.dependencies.TokenAuthHandler.TokenAuthHandler import TokenAuthHandler
from aihub_lib.infrastructure.api.AIHubSettings import AIHubSettings
from aihub_lib.infrastructure.mongo.MongoSettings import MongoSettings
from aihub_lib.persistence.access.entities.BearerToken import BearerToken
from aihub_lib.persistence.user.UserEntity import UserEntity
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from mongoengine import connect, disconnect

from aihub_api.routes.user.UserController import UserController
from aihub_api.testing.ApiTestRunner import ApiTestRunner

BASE_URL = "http://test"
USER_ENDPOINT = "/user/me"
EXPECTED_USER_FIELDS = ["id", "name", "email", "roles", "profile_image", "favorite_modules"]


@pytest.fixture
def mongo_db():
    """Set up and tear down the MongoDB connection for tests."""
    connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
        uuidRepresentation="standard",
    )
    yield
    disconnect()


@pytest.fixture
def valid_token(mongo_db):
    """Insert a valid token document and return its token string."""
    user = UserEntity.create_user(
        oid=os.getenv("OID", DangerousDevelopmentOnlyAuthSettings().OID),
        name=os.getenv("NAME", DangerousDevelopmentOnlyAuthSettings().NAME),
        email=os.getenv("EMAIL", DangerousDevelopmentOnlyAuthSettings().EMAIL),
        roles=DangerousDevelopmentOnlyAuthSettings().ROLES,
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
        "id": os.getenv("OID", DangerousDevelopmentOnlyAuthSettings().OID),
        "name": os.getenv("NAME", DangerousDevelopmentOnlyAuthSettings().NAME),
        "email": os.getenv("EMAIL", DangerousDevelopmentOnlyAuthSettings().EMAIL),
        "profile_image": None,
        "roles": DangerousDevelopmentOnlyAuthSettings().ROLES,
        "favorite_modules": [],
    }


@pytest_asyncio.fixture(scope="module")
async def token_api_client():
    """Create a TestClient with UserController mounted using TokenAuthHandler."""
    runner = ApiTestRunner()
    auth = TokenAuthHandler()
    runner.mount(UserController(auth=auth).get_my_user())
    app = runner.create_app()
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
