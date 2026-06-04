import pytest
from fastapi.testclient import TestClient
from swiss_ai_hub.core.infrastructure import AIHubSettings
from swiss_ai_hub.core.routes import HealthController
from swiss_ai_hub.core.testing.auth_utils import TestAuthHandler

from swiss_ai_hub.api.runners.api_test_runner import ApiTestRunner

BASE_ENDPOINT = "/api/v1/health"
EXPECTED_STATUS = "ok"


@pytest.fixture
def api_client():
    """Fixture to create a test client for the API."""
    auth = TestAuthHandler()
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


def test_health_endpoint_includes_version(api_client):
    """The health response must surface the running service version so it is checkable programmatically."""
    response = api_client.get(BASE_ENDPOINT, headers={"Content-Type": "application/json"})

    data = response.json()
    assert data.get("version") == AIHubSettings().VERSION


def test_openapi_documents_service_version():
    """The API documentation (OpenAPI spec) must expose the running service version."""
    runner = ApiTestRunner()
    app = runner.create_app()
    api_app = next(route.app for route in app.routes if getattr(route, "path", None) == runner.api_path)

    assert api_app.openapi()["info"]["version"] == AIHubSettings().VERSION
