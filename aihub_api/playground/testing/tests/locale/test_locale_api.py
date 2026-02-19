import pytest
import pytest_asyncio
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthHandler import (
    DangerousDevelopmentOnlyAuthHandler,
)
from aihub_lib.auth.identity.DangerousDevelopmentOnlyIdentityProvider.DangerousDevelopmentOnlyIdentityProvider import (
    DangerousDevelopmentOnlyIdentityProvider,
)
from aihub_lib.testing.auth_utils.role_mocks import mock_role_entity_methods  # noqa: F401
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from aihub_api.routes.i18n.I18nController import I18nController
from aihub_api.runners.ApiTestRunner import ApiTestRunner

BASE_URL = "http://test"
API_ENDPOINT = "/api/v1/i18n/my-locale"
DEFAULT_LANG_KEY = "lang"


@pytest_asyncio.fixture(scope="module")
async def api_client():
    """Create an API client with I18nController mounted using DangerousDevelopmentOnlyAuthHandler."""
    auth = DangerousDevelopmentOnlyAuthHandler(identity_provider=DangerousDevelopmentOnlyIdentityProvider())
    controller = I18nController(auth=auth).get_my_locale()
    runner = ApiTestRunner()
    runner.mount(controller)
    app = runner.create_app()
    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url=BASE_URL) as client:
            yield client


@pytest.mark.parametrize(
    "headers, params, expected_locale",
    [
        ({"Accept-Language": "en"}, None, "en"),
        ({"Accept-Language": "en-US"}, None, "en"),
        ({"Accept-Language": "fr, en"}, None, "fr"),
        ({"Accept-Language": "es"}, None, "de"),
        ({"lang": "it"}, None, "it"),
        ({"locale": "fr"}, None, "fr"),
        (None, {"locale": "it"}, "it"),
        (None, {"locale": "es"}, "de"),
        ({"Accept-Language": "es"}, {"locale": "en"}, "de"),
        ({"locale": "fr"}, {"locale": "it"}, "fr"),
    ],
)
@pytest.mark.asyncio
async def test_get_locale_parametrized(api_client, headers, params, expected_locale):
    """Test /api/v1/i18n/my-locale with various header and query parameter configurations."""
    response = await api_client.get(API_ENDPOINT, headers=headers, params=params)
    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()
    assert (
        data.get(DEFAULT_LANG_KEY) == expected_locale
    ), f"Expected locale '{expected_locale}', got '{data.get(DEFAULT_LANG_KEY)}'"
    assert "test" in data and data["test"]
