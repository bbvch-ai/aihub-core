import os
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from mongoengine import connect, disconnect

from aihub_api.runners.ApiTestRunner import ApiTestRunner
from aihub_api.routes.user.UserController import UserController
from aihub_lib.auth.dependencies.TokenAuthHandler.TokenAuthHandler import TokenAuthHandler
from aihub_lib.infrastructure.azure.cosmos.CosmosAccess import CosmosAccess
from aihub_lib.persistence.access.entities.BearerToken import BearerToken, ApiUser

USER_ENDPOINT = "/api/v1/user/me"
EXPECTED_USER_FIELDS = ["id", "name", "email"]


@pytest.fixture(scope="module", autouse=True)
def mongo_db():
    """Set up and tear down the MongoDB connection for tests."""
    connect(db="aihub", host=CosmosAccess().get_connection_string())
    yield
    disconnect()


@pytest.fixture
def valid_token(mongo_db):
    """Insert a valid token document and return its token string."""
    api_user = ApiUser(
        oid=os.getenv("OID", "1234567890"),
        name=os.getenv("NAME", "Melanie Musterfrau"),
        preferred_username=os.getenv("EMAIL", "melanie.musterfrau@bbv.ch"),
        roles=["AllAgents"],
    )
    expiry = datetime.now(timezone.utc) + timedelta(hours=1)
    token_obj = BearerToken.create_new_token(
        name="token-name",
        expiry_date=expiry,
        user=api_user,
        roles=["AllAgents"],
    )
    yield token_obj.token
    token_obj.delete()


@pytest.fixture
def expected_user_data():
    """Return the expected user data based on environment variables."""
    return {
        "id": os.getenv("OID", "1234567890"),
        "name": os.getenv("NAME", "Melanie Musterfrau"),
        "email": os.getenv("EMAIL", "melanie.musterfrau@bbv.ch"),
        "profile_image": None,
    }


@pytest.fixture
def token_api_client():
    """Create a TestClient with UserController mounted using TokenAuthHandler."""
    runner = ApiTestRunner()
    auth = TokenAuthHandler()
    runner.mount(UserController(auth=auth).get_user())
    return TestClient(runner.get_app())


def test_get_user_with_valid_token(token_api_client, valid_token, expected_user_data):
    """Test GET /user/me with a valid token returns expected user data."""
    headers = {
        "Authorization": f"Bearer {valid_token}",
        "Content-Type": "application/json",
    }
    response = token_api_client.get(USER_ENDPOINT, headers=headers)
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.text}"
    user_data = response.json()
    assert all(key in user_data for key in EXPECTED_USER_FIELDS)
    assert user_data == expected_user_data


def test_get_user_with_invalid_token(token_api_client):
    """Test GET /user/me with an invalid token returns 401 or 403."""
    headers = {
        "Authorization": "Bearer invalid.token.value",
        "Content-Type": "application/json",
    }
    response = token_api_client.get(USER_ENDPOINT, headers=headers)
    assert response.status_code in (
        401,
        403,
    ), f"Expected 401/403 for invalid token but got {response.status_code}: {response.text}"
