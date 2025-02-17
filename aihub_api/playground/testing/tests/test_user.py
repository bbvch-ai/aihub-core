import pytest
from fastapi.testclient import TestClient

from aihub_api.runners.ApiTestRunner import ApiTestRunner
from aihub_lib.auth.dependencies.NoAuthHandler.NoAuthHandler import NoAuthHandler
from aihub_lib.routes.health.HealthController import HealthController


@pytest.fixture(scope="module")
def app():
    runner = ApiTestRunner()
    auth = NoAuthHandler()

    runner.mount(
        HealthController(auth=auth).get_health(),
    )

    # Use the underlying FastAPI app
    app = runner.get_app()  # You could expose this via a public method if desired
    return TestClient(app)


@pytest.mark.asyncio
async def test_get_current_user(app):
    """
    Test the /api/v1/user/me endpoint to ensure it returns the expected user data.
    """
    response = app.get(
        "/api/v1/health",
        headers={"Accept": "application/json"}
    )
    assert response.status_code == 200, "Expected status code 200"

    body = response.json()
    assert body.get("status") == "ok", "Expected name to be 'Melanie Musterfrau'"
