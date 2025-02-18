import pytest
from fastapi.testclient import TestClient

from aihub_api.runners.ApiTestRunner import ApiTestRunner
from aihub_lib.routes.health.HealthController import HealthController


@pytest.fixture
def api_client():
    """Fixture to create a test client for the API."""
    runner = ApiTestRunner()
    runner.mount(HealthController().get_health())
    return TestClient(runner.get_app())


def test_health_endpoint(api_client):
    """
    Test the health endpoint returns the expected response.

    Ensures that:
    1. The endpoint returns a 200 status code
    2. The response contains the expected 'status: ok' message
    """
    # Given
    endpoint = "/api/v1/health"
    headers = {"Content-Type": "application/json"}

    # When
    response = api_client.get(endpoint, headers=headers)

    # Then
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"

    data = response.json()
    assert "status" in data, "Response missing 'status' field"
    assert data["status"] == "ok", f"Expected status 'ok', got '{data.get('status')}'"