import pytest
from fastapi.testclient import TestClient
from aihub_api.runners.ApiTestRunner import ApiTestRunner
from aihub_api.routes.user.UserController import UserController
from aihub_lib.auth.dependencies.NoAuthHandler.NoAuthHandler import NoAuthHandler
import os


@pytest.fixture
def api_client():
    """Fixture to create a test client for the API with UserController mounted."""
    runner = ApiTestRunner()
    auth = NoAuthHandler()
    runner.mount(UserController(auth=auth).get_user())
    return TestClient(runner.get_app())


@pytest.fixture
def expected_user_data():
    """Fixture containing the expected user data from environment variables."""
    return {
        "id": os.getenv("OID", "1234567890"),
        "name": os.getenv("NAME", "Melanie Musterfrau"),
        "email": os.getenv("EMAIL", "melanie.musterfrau@bbv.ch")
    }


def test_get_user_endpoint(api_client, expected_user_data):
    """
    Test the user endpoint returns the correct user data.

    Ensures that:
    1. The endpoint returns a 200 status code
    2. The response contains all required user fields
    3. The user data matches the expected values from environment
    """
    # Given
    endpoint = "/api/v1/user/me"
    headers = {"Content-Type": "application/json"}

    # When
    response = api_client.get(endpoint, headers=headers)

    # Then
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"

    user_data = response.json()

    # Check structure
    assert isinstance(user_data, dict), "Response should be a dictionary"
    assert all(key in user_data for key in ["id", "name", "email"]), "Missing required user fields"

    # Check values
    assert user_data == expected_user_data, "User data doesn't match expected values"


def test_user_dto_structure(api_client):
    """
    Test that the UserDTO response matches the expected structure.
    """
    # Given
    endpoint = "/api/v1/user/me"

    # When
    response = api_client.get(endpoint)
    user_data = response.json()

    # Then
    assert isinstance(user_data["id"], str), "User ID should be a string"
    assert isinstance(user_data["name"], str), "User name should be a string"
    assert isinstance(user_data["email"], str), "User email should be a string"
    assert "@" in user_data["email"], "Email should be in valid format"


@pytest.mark.parametrize("headers", [
    {"Content-Type": "application/json"},
    {"Accept": "application/json"},
    {},  # Test without headers
])
def test_user_endpoint_different_headers(api_client, headers):
    """Test the user endpoint with different header configurations."""
    endpoint = "/api/v1/user/me"
    response = api_client.get(endpoint, headers=headers)

    assert response.status_code == 200
    assert "id" in response.json()