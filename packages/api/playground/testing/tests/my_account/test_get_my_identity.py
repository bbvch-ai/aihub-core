import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from swiss_ai_hub.core.testing.auth_utils import TestAuthHandler
from swiss_ai_hub.core.testing.auth_utils.test_identity import TEST_USER_EMAIL, TEST_USER_NAME, TEST_USER_OID

from swiss_ai_hub.api.routes.my_account.my_account_controller import MyAccountController
from swiss_ai_hub.api.runners.api_test_runner import ApiTestRunner

pytestmark = pytest.mark.beanie

BASE_URL = "http://test"
ENDPOINT = "/api/v1/active/my-account/identity"


@pytest_asyncio.fixture(scope="module", loop_scope="session")
async def api_client(beanie_test_database):
    runner = ApiTestRunner()
    auth = TestAuthHandler()
    runner.mount(MyAccountController(auth=auth).get_my_identity())
    app = runner.create_app()
    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url=BASE_URL) as client:
            yield client


async def test_returns_user_identity_without_access_field(api_client):
    response = await api_client.get(ENDPOINT)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == TEST_USER_OID
    assert data["name"] == TEST_USER_NAME
    assert data["email"] == TEST_USER_EMAIL
    # The whole point of the identity endpoint: no access matrix.
    assert "access" not in data


async def test_carries_is_sys_admin_flag(api_client):
    response = await api_client.get(ENDPOINT)
    assert response.status_code == 200
    # TestAuthHandler default identity is non-sysadmin.
    assert response.json()["is_sys_admin"] is False


async def test_carries_roles_from_token(api_client):
    response = await api_client.get(ENDPOINT)
    assert response.status_code == 200
    roles = response.json()["roles"]
    assert isinstance(roles, list)
    assert "TestOnlyFullAdminAccess" in roles


async def test_includes_dashboard(api_client):
    response = await api_client.get(ENDPOINT)
    assert response.status_code == 200
    assert "dashboard" in response.json()
