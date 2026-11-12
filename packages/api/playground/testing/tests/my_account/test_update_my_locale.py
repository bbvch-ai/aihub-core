import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from swiss_ai_hub.core.auth import KeycloakAdminService
from swiss_ai_hub.core.testing.auth_utils import TestAuthHandler
from swiss_ai_hub.core.testing.auth_utils.test_identity import TEST_USER_OID

from swiss_ai_hub.api.routes.my_account.my_account_controller import MyAccountController
from swiss_ai_hub.api.runners.api_test_runner import ApiTestRunner

pytestmark = pytest.mark.beanie

BASE_URL = "http://test"
ENDPOINT = "/api/v1/active/my-account/locale"


@pytest_asyncio.fixture(scope="module", loop_scope="session")
async def api_client(beanie_test_database):
    runner = ApiTestRunner()
    auth = TestAuthHandler()
    runner.mount(MyAccountController(auth=auth).update_my_locale())
    app = runner.create_app()
    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url=BASE_URL) as client:
            yield client


@pytest.mark.parametrize("locale", ["de", "en", "fr", "it"])
async def test_persists_every_supported_locale(api_client, locale):
    response = await api_client.put(ENDPOINT, json={"locale": locale})

    assert response.status_code == 204, response.text
    assert await KeycloakAdminService.get_preferred_locale(TEST_USER_OID) == locale


async def test_last_write_wins(api_client):
    await api_client.put(ENDPOINT, json={"locale": "de"})
    await api_client.put(ENDPOINT, json={"locale": "fr"})

    assert await KeycloakAdminService.get_preferred_locale(TEST_USER_OID) == "fr"


@pytest.mark.parametrize("locale", ["es", "DE", "en-GB", ""])
async def test_rejects_unsupported_locale(api_client, locale):
    response = await api_client.put(ENDPOINT, json={"locale": locale})

    assert response.status_code == 422, response.text


async def test_rejected_locale_is_not_persisted(api_client):
    await api_client.put(ENDPOINT, json={"locale": "en"})

    await api_client.put(ENDPOINT, json={"locale": "es"})

    assert await KeycloakAdminService.get_preferred_locale(TEST_USER_OID) == "en"
