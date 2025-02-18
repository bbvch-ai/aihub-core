import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import AsyncClient, ASGITransport

from aihub_api.runners.ApiTestRunner import ApiTestRunner
from aihub_api.routes.i18n.I18nController import I18nController
from aihub_lib.auth.dependencies.NoAuthHandler.NoAuthHandler import NoAuthHandler


@pytest_asyncio.fixture(scope="module")
async def api_client():
    """
    Creates an end‑to‑end API client with the I18nController mounted.
    Uses NoAuthHandler so that authentication is bypassed.
    """
    auth = NoAuthHandler()
    controller = I18nController(auth=auth).get_my_locale()
    runner = ApiTestRunner()
    runner.mount(controller)
    app = runner.get_app()

    async with LifespanManager(app) as lifespan:
        async with AsyncClient(
            transport=ASGITransport(app=lifespan.app), base_url="http://test"
        ) as client:
            yield client


@pytest.mark.parametrize(
    "headers, params, expected_locale",
    [
        # Only Accept-Language header provided
        ({"Accept-Language": "en"}, None, "en"),
        ({"Accept-Language": "en-US"}, None, "en"),  # Should extract "en"
        ({"Accept-Language": "fr, en"}, None, "fr"),
        ({"Accept-Language": "es"}, None, "de"),  # Unknown language, fallback to default "de"
        # Alternative headers take precedence
        ({"lang": "it"}, None, "it"),
        ({"locale": "fr"}, None, "fr"),
        # Using query parameters (if no header is provided)
        (None, {"locale": "it"}, "it"),
        (None, {"locale": "es"}, "de"),  # "es" not in whitelist, so fallback to "de"
        # When both header and query parameter are provided, header wins
        ({"Accept-Language": "es"}, {"locale": "en"}, "de"),
        ({"locale": "fr"}, {"locale": "it"}, "fr"),
    ],
)
@pytest.mark.asyncio
async def test_get_locale_parametrized(api_client, headers, params, expected_locale):
    """
    Test the /api/v1/i18n/my-locale endpoint using different headers and query parameter configurations.
    The middleware should pick the correct locale (or fall back) according to the priority:
        lang header > locale header > Accept-Language header > path params > query params > default.
    """
    response = await api_client.get("/api/v1/i18n/my-locale", headers=headers, params=params)
    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()
    assert data.get("lang") == expected_locale, f"Expected locale '{expected_locale}', got '{data.get('lang')}'"
    assert "test" in data and data["test"]
