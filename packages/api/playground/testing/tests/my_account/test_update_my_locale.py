import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from mongoengine import connect, disconnect
from swiss_ai_hub.core.auth import KeycloakAdminService
from swiss_ai_hub.core.infrastructure import AIHubSettings, MongoSettings
from swiss_ai_hub.core.testing.auth_utils import TestAuthHandler
from swiss_ai_hub.core.testing.auth_utils.test_identity import TEST_USER_OID

from swiss_ai_hub.api.routes.my_account.my_account_controller import MyAccountController
from swiss_ai_hub.api.runners.api_test_runner import ApiTestRunner

pytestmark = pytest.mark.usefixtures("mongo_db")

BASE_URL = "http://test"
ENDPOINT = "/api/v1/active/my-account/locale"


@pytest.fixture(scope="module")
def mongo_db():
    connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
        uuidRepresentation="standard",
    )
    yield
    disconnect()


@pytest_asyncio.fixture(scope="module")
async def api_client():
    runner = ApiTestRunner()
    auth = TestAuthHandler()
    runner.mount(MyAccountController(auth=auth).update_my_locale())
    app = runner.create_app()
    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url=BASE_URL) as client:
            yield client


@pytest.mark.asyncio
@pytest.mark.parametrize("locale", ["de", "en", "fr", "it"])
async def test_persists_every_supported_locale(api_client, locale):
    response = await api_client.put(ENDPOINT, json={"locale": locale})

    assert response.status_code == 204, response.text
    assert await KeycloakAdminService.get_preferred_locale(TEST_USER_OID) == locale


@pytest.mark.asyncio
async def test_last_write_wins(api_client):
    await api_client.put(ENDPOINT, json={"locale": "de"})
    await api_client.put(ENDPOINT, json={"locale": "fr"})

    assert await KeycloakAdminService.get_preferred_locale(TEST_USER_OID) == "fr"


@pytest.mark.asyncio
@pytest.mark.parametrize("locale", ["es", "DE", "en-GB", ""])
async def test_rejects_unsupported_locale(api_client, locale):
    response = await api_client.put(ENDPOINT, json={"locale": locale})

    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_rejected_locale_is_not_persisted(api_client):
    await api_client.put(ENDPOINT, json={"locale": "en"})

    await api_client.put(ENDPOINT, json={"locale": "es"})

    assert await KeycloakAdminService.get_preferred_locale(TEST_USER_OID) == "en"
