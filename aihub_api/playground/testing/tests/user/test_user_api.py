import pytest
import pytest_asyncio
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthHandler import (
    DangerousDevelopmentOnlyAuthHandler,
)
from aihub_lib.infrastructure.api.AIHubSettings import AIHubSettings
from aihub_lib.infrastructure.mongo.MongoSettings import MongoSettings
from aihub_lib.testing.auth_utils.role_mocks import mock_role_entity_methods  # noqa: F401
from aihub_lib.testing.auth_utils.tenant_mocks import mock_tenant_entity_autouse  # noqa: F401
from aihub_lib.testing.auth_utils.user_mocks import get_expected_user_data, mock_user_entity_autouse  # noqa: F401
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
    connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
        uuidRepresentation="standard",
    )
    yield
    disconnect()


@pytest_asyncio.fixture(scope="module")
async def api_client():
    """Create a test client for the API with UserController mounted."""
    runner = ApiTestRunner()
    auth = DangerousDevelopmentOnlyAuthHandler()
    runner.mount(UserController(auth=auth).get_my_user())
    app = runner.create_app()
    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url=BASE_URL) as client:
            yield client


@pytest.mark.asyncio
async def test_get_user_endpoint(api_client):
    """Test GET /user/me returns expected user data."""
    headers = {"Content-Type": "application/json"}
    response = await api_client.get(USER_ENDPOINT, headers=headers)
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    user_data = response.json()
    user_data["access"]["agents"] = []
    user_data["access"]["processes"] = []
    for child in user_data["dashboard"]["children"]:
        del child["id"]
    assert isinstance(user_data, dict)
    assert all(key in user_data for key in EXPECTED_USER_FIELDS)

    # Get expected user data from the shared function
    expected_data = get_expected_user_data()
    assert user_data == expected_data


@pytest.mark.asyncio
async def test_user_dto_structure(api_client):
    """Test that user DTO has the expected structure."""
    response = await api_client.get(USER_ENDPOINT)
    user_data = response.json()
    assert isinstance(user_data["id"], str)
    assert isinstance(user_data["name"], str)
    assert isinstance(user_data["email"], str)
    assert "@" in user_data["email"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "headers",
    [
        {"Content-Type": "application/json"},
        {"Accept": "application/json"},
        {},
    ],
)
async def test_user_endpoint_different_headers(api_client, headers):
    """Test GET /user/me with various headers."""
    response = await api_client.get(USER_ENDPOINT, headers=headers)
    assert response.status_code == 200
    assert "id" in response.json()
