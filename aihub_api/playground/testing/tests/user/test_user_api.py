import os
import pytest
from fastapi.testclient import TestClient

from aihub_api.runners.ApiTestRunner import ApiTestRunner
from aihub_api.routes.user.UserController import UserController
from aihub_lib.auth.dependencies.NoAuthHandler.NoAuthHandler import NoAuthHandler

USER_ENDPOINT = "/api/v1/user/me"
EXPECTED_USER_FIELDS = ["id", "name", "email"]


@pytest.fixture
def api_client():
    """Create a test client for the API with UserController mounted."""
    runner = ApiTestRunner()
    auth = NoAuthHandler()
    runner.mount(UserController(auth=auth).get_user())
    return TestClient(runner.get_app())


@pytest.fixture
def expected_user_data():
    """Expected user data from environment variables."""
    return {
        "id": os.getenv("OID", "1234567890"),
        "name": os.getenv("NAME", "Melanie Musterfrau"),
        "email": os.getenv("EMAIL", "melanie.musterfrau@bbv.ch"),
    }


def test_get_user_endpoint(api_client, expected_user_data):
    """Test GET /user/me returns expected user data."""
    headers = {"Content-Type": "application/json"}
    response = api_client.get(USER_ENDPOINT, headers=headers)
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    user_data = response.json()
    assert isinstance(user_data, dict)
    assert all(key in user_data for key in EXPECTED_USER_FIELDS)
    assert user_data == expected_user_data


def test_user_dto_structure(api_client):
    """Test that user DTO has the expected structure."""
    response = api_client.get(USER_ENDPOINT)
    user_data = response.json()
    assert isinstance(user_data["id"], str)
    assert isinstance(user_data["name"], str)
    assert isinstance(user_data["email"], str)
    assert "@" in user_data["email"]


@pytest.mark.parametrize(
    "headers",
    [
        {"Content-Type": "application/json"},
        {"Accept": "application/json"},
        {},
    ],
)
def test_user_endpoint_different_headers(api_client, headers):
    """Test GET /user/me with various headers."""
    response = api_client.get(USER_ENDPOINT, headers=headers)
    assert response.status_code == 200
    assert "id" in response.json()
