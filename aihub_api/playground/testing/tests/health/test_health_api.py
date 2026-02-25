import pytest
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthHandler import (
    DangerousDevelopmentOnlyAuthHandler,
)
from aihub_lib.routes.health.HealthController import HealthController
from aihub_lib.testing.auth_utils.tenant_mocks import mock_tenant_entity_autouse  # noqa: F401
from aihub_lib.testing.auth_utils.user_mocks import mock_user_entity_autouse  # noqa: F401
from fastapi.testclient import TestClient

from aihub_api.runners.ApiTestRunner import ApiTestRunner

BASE_ENDPOINT = "/api/v1/health"
EXPECTED_STATUS = "ok"


@pytest.fixture
def api_client():
    """Fixture to create a test client for the API."""
    auth = DangerousDevelopmentOnlyAuthHandler()
    runner = ApiTestRunner()
    runner.mount(HealthController(auth=auth).get_health())
    return TestClient(runner.create_app())


def test_health_endpoint(api_client):
    """Test that the health endpoint returns a 200 status code and 'status: ok' message."""
    headers = {"Content-Type": "application/json"}
    response = api_client.get(BASE_ENDPOINT, headers=headers)
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"

    data = response.json()
    assert data.get("status") == EXPECTED_STATUS, f"Expected status '{EXPECTED_STATUS}', got '{data.get('status')}'"
