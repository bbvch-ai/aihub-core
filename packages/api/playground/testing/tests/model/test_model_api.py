"""`GET /models/mode/{mode}` over HTTP: the requirement query parameters parse as a model picker sends them."""

from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from mongoengine import connect, disconnect
from swiss_ai_hub.core.infrastructure import AIHubSettings, MongoSettings
from swiss_ai_hub.core.testing.auth_utils import TestAuthHandler

from playground.testing.tests.model.fake_models import FAKE_MODELS
from swiss_ai_hub.api.routes.model.model_controller import ModelController
from swiss_ai_hub.api.routes.model.model_service import ModelService
from swiss_ai_hub.api.runners.api_test_runner import ApiTestRunner

pytestmark = pytest.mark.usefixtures("mongo_db")

CHAT_MODELS_ENDPOINT = "/api/v1/active/models/mode/chat"


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
    runner.mount(ModelController(auth=TestAuthHandler()).get_litellm_models_by_mode().get_litellm_model())
    app = runner.create_app()
    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url="http://test") as client:
            yield client


async def _listed(api_client: AsyncClient, params: list[tuple[str, str]]) -> list[str]:
    with patch.object(ModelService, "get_model_list", AsyncMock(return_value=FAKE_MODELS)):
        response = await api_client.get(CHAT_MODELS_ENDPOINT, params=params)
    assert response.status_code == 200, response.text
    return [model["model_name"] for model in response.json()]


@pytest.mark.asyncio(loop_scope="module")
async def test_repeated_parameters_are_all_applied(api_client):
    listed = await _listed(
        api_client,
        [
            ("capability", "tool_calling"),
            ("capability", "vision"),
            ("hosting_location", "eu"),
            ("hosting_location", "swiss_cloud"),
        ],
    )
    assert set(listed) == {"text-generation/fake-swiss", "text-generation/fake-eu"}


@pytest.mark.asyncio(loop_scope="module")
async def test_without_parameters_the_ocr_model_is_left_out(api_client):
    listed = await _listed(api_client, [])
    assert "text-generation/fake-ocr" not in listed
    assert "text-generation/fake-undeclared" in listed


@pytest.mark.asyncio(loop_scope="module")
async def test_include_special_purpose_lists_the_ocr_model(api_client):
    assert "text-generation/fake-ocr" in await _listed(api_client, [("include_special_purpose", "true")])


@pytest.mark.asyncio(loop_scope="module")
async def test_each_listed_model_carries_its_display_name(api_client):
    with patch.object(ModelService, "get_model_list", AsyncMock(return_value=FAKE_MODELS)):
        response = await api_client.get(CHAT_MODELS_ENDPOINT)
    assert {model["display_name"] for model in response.json()} >= {"fake-swiss", "fake-undeclared"}


@pytest.mark.asyncio(loop_scope="module")
@pytest.mark.parametrize("parameter", ["capability", "hosting_location"])
async def test_an_unknown_value_is_a_422(api_client, parameter):
    response = await api_client.get(CHAT_MODELS_ENDPOINT, params={parameter: "teleportation"})
    assert response.status_code == 422
