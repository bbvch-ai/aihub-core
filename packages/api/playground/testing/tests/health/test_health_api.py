import pytest
from fastapi.testclient import TestClient
from swiss_ai_hub.core.dependencies import use_nats
from swiss_ai_hub.core.infrastructure import AIHubSettings, use_milvus, use_redis, use_s3
from swiss_ai_hub.core.routes import HealthController
from swiss_ai_hub.core.testing.auth_utils import TestAuthHandler

from swiss_ai_hub.api.routes.health.api_health_controller import ApiHealthController
from swiss_ai_hub.api.runners.api_test_runner import ApiTestRunner

BASE_ENDPOINT = "/api/v1/health"
EXPECTED_STATUS = "ok"
EXPECTED_VERSION = AIHubSettings().VERSION


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
    assert data.get("version") == EXPECTED_VERSION


def test_ready_endpoint_includes_version():
    """The readiness endpoint must report the running service version regardless of dependency health."""
    auth = TestAuthHandler()
    runner = ApiTestRunner()
    runner.mount(ApiHealthController(auth=auth).get_ready())

    # The dependency providers read live clients from ``app.state`` (populated by the lifetime
    # manager in production). Override them to ``None`` so the readiness checks run without real
    # infrastructure: every check reports unhealthy, but the version must still be surfaced.
    runner._api_app.dependency_overrides[use_nats] = lambda: None
    runner._api_app.dependency_overrides[use_redis] = lambda: None
    runner._api_app.dependency_overrides[use_milvus] = lambda: None
    runner._api_app.dependency_overrides[use_s3] = lambda: None

    client = TestClient(runner.create_app())
    response = client.get(f"{BASE_ENDPOINT}/ready")

    assert response.json().get("version") == EXPECTED_VERSION


def test_openapi_documents_service_version():
    """The API documentation (OpenAPI spec) must expose the running service version."""
    runner = ApiTestRunner()
    app = runner.create_app()
    mounted_apps = [route.app for route in app.routes if getattr(route, "path", None) == runner.api_path]
    assert mounted_apps, f"No application mounted at {runner.api_path}"
    api_app = mounted_apps[0]

    assert api_app.openapi()["info"]["version"] == EXPECTED_VERSION
