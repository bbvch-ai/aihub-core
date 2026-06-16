import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from mongoengine import connect, disconnect
from swiss_ai_hub.core.infrastructure import AIHubSettings, MongoSettings
from swiss_ai_hub.core.testing.auth_utils import TEST_TENANT_ID, TestAuthHandler

from swiss_ai_hub.api.routes.role.role_controller import RoleController
from swiss_ai_hub.api.runners.api_test_runner import ApiTestRunner

BASE_URL = "http://test"
CAPABILITIES_URL = f"/api/v1/{TEST_TENANT_ID}/roles/access/capabilities"


@pytest.fixture(scope="function")
def mongo_db():
    connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
        uuidRepresentation="standard",
    )
    yield
    disconnect()


@pytest_asyncio.fixture(scope="function")
async def api_client(mongo_db):
    runner = ApiTestRunner()
    runner.mount(RoleController(auth=TestAuthHandler()).get_access_capabilities())
    app = runner.create_app()
    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url=BASE_URL) as client:
            yield client


@pytest.mark.asyncio
async def test_non_sysadmin_caller_cannot_claim_sysadmin_in_the_catalog(api_client):
    # The default test identity is a (non-sysadmin) tenant role admin. Sending is_sys_admin=true and
    # restrict_to_tenant=false must NOT flip the catalog to "everything granted" — the acting identity
    # decides those privileges, not the request body. Empty draft rules must therefore grant nothing.
    response = await api_client.post(
        CAPABILITIES_URL,
        json={"access_rules": [], "is_sys_admin": True, "restrict_to_tenant": False},
    )

    assert response.status_code == 200
    capabilities = [capability for group in response.json()["groups"] for capability in group["capabilities"]]
    assert capabilities  # the role service gate is present in the catalog
    assert not any(capability["granted"] for capability in capabilities)
