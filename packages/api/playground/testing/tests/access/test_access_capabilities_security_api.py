import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from mongoengine import connect, disconnect
from starlette.requests import Request
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.infrastructure import AIHubSettings, MongoSettings
from swiss_ai_hub.core.testing.auth_utils import TEST_TENANT_ID, TestAuthHandler, fake_user

from swiss_ai_hub.api.routes.access.access_controller import AccessController
from swiss_ai_hub.api.runners.api_test_runner import ApiTestRunner

BASE_URL = "http://test"
CAPABILITIES_URL = f"/api/v1/{TEST_TENANT_ID}/access/capabilities"


class _SysAdminAuthHandler(TestAuthHandler):
    """Acts as a platform sysadmin so the symmetric escalation path can be exercised."""

    async def authenticate_token(self, token_str: str, request: Request | None = None) -> UserIdentity:
        return fake_user(is_sys_admin=True)


def _capabilities_client(auth: TestAuthHandler):
    runner = ApiTestRunner()
    runner.mount(AccessController(auth=auth).get_access_capabilities())
    return runner.create_app()


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
    async with LifespanManager(_capabilities_client(TestAuthHandler())) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url=BASE_URL) as client:
            yield client


@pytest_asyncio.fixture(scope="function")
async def sysadmin_api_client(mongo_db):
    async with LifespanManager(_capabilities_client(_SysAdminAuthHandler())) as lifespan:
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


@pytest.mark.asyncio
async def test_sysadmin_caller_does_get_the_full_granted_catalog(sysadmin_api_client):
    # The symmetric path: when the acting identity *is* a sysadmin, is_sys_admin=true takes effect and the
    # catalog is fully granted from empty draft rules — so a future refactor that hardcodes is_sys_admin=False
    # on the server (silently stripping sysadmins of their full view) fails here.
    response = await sysadmin_api_client.post(
        CAPABILITIES_URL,
        json={"access_rules": [], "is_sys_admin": True, "restrict_to_tenant": False},
    )

    assert response.status_code == 200
    capabilities = [capability for group in response.json()["groups"] for capability in group["capabilities"]]
    assert capabilities
    assert all(capability["granted"] for capability in capabilities)
