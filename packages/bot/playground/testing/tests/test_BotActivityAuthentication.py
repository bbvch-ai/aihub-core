"""Inbound activities must carry a Bot Framework token issued for the bot configured on the request path."""

import time
from unittest.mock import AsyncMock, MagicMock

import jwt
import pytest
import pytest_asyncio
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import FastAPI, Request, Response
from httpx import ASGITransport, AsyncClient
from microsoft_agents.hosting.core import TurnContext
from swiss_ai_hub.core.dependencies import use_nats
from swiss_ai_hub.core.distributor import use_external_agent_event_distributor
from swiss_ai_hub.core.testing.auth_utils import TestAuthHandler

from playground.testing.tests.bot_framework_token_factory import BotFrameworkTokenFactory
from swiss_ai_hub.bot.persistence.entities.path_entity import Credentials
from swiss_ai_hub.bot.routes.bot_in_the_loop.bot_in_the_loop_controller import BotInTheLoopController
from swiss_ai_hub.bot.routes.bot_in_the_loop.bot_in_the_loop_handler import BotInTheLoopHandler
from swiss_ai_hub.bot.routes.routes_service import RoutesService

APP_ID = "bot-app-id"
TENANT_ID = "bot-tenant-id"
ROUTE = "/api/v1/agent/chat/completions/Agent/agent-1/json"
SERVICE_URL = "https://smba.trafficmanager.net/emea/"
BOT_FRAMEWORK_ISSUER = BotFrameworkTokenFactory.BOT_FRAMEWORK_ISSUER


def _token(private_key: rsa.RSAPrivateKey | None = None, **overrides: object) -> str:
    return BotFrameworkTokenFactory.token(app_id=APP_ID, service_url=SERVICE_URL, private_key=private_key, **overrides)


def _activity(service_url: str = SERVICE_URL) -> dict:
    return {
        "type": "message",
        "channelId": "msteams",
        "serviceUrl": service_url,
        "conversation": {"id": "conversation-1"},
        "from": {"id": "29:user", "name": "victim@example.com"},
        "recipient": {"id": "28:bot"},
        "text": "hi",
    }


@pytest.fixture
def configured_bot(monkeypatch: pytest.MonkeyPatch) -> None:
    BotFrameworkTokenFactory.trust_signing_key(monkeypatch)
    monkeypatch.setattr(RoutesService, "_adapter_cache", {})
    monkeypatch.setattr(
        RoutesService,
        "get_credentials",
        MagicMock(
            return_value=Credentials(
                APP_TYPE="SingleTenant", APP_ID=APP_ID, APP_PASSWORD="secret", APP_TENANTID=TENANT_ID
            )
        ),
    )


@pytest.fixture
def adapter(monkeypatch: pytest.MonkeyPatch, configured_bot: None) -> MagicMock:
    fake_adapter = MagicMock()

    async def _process(request: Request, agent: object) -> Response:
        fake_adapter.claims_identity = request.get("claims_identity")
        return Response(status_code=202)

    fake_adapter.process = AsyncMock(side_effect=_process)
    monkeypatch.setattr(RoutesService, "get_adapter", MagicMock(return_value=fake_adapter))
    return fake_adapter


@pytest_asyncio.fixture
async def client(configured_bot: None) -> AsyncClient:
    app = FastAPI()
    echo_agent = MagicMock()

    async def _echo(turn_context: TurnContext) -> None:
        await turn_context.send_activity("pong")

    echo_agent.on_turn = _echo

    @app.post(ROUTE)
    async def activity_route(request: Request) -> Response:
        return await RoutesService.process_activity(request, echo_agent)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as async_client:
        yield async_client


async def _post(client: AsyncClient, token: str | None, activity: dict | None = None) -> int:
    headers = {"Authorization": f"Bearer {token}"} if token is not None else {}
    response = await client.post(ROUTE, json=activity or _activity(), headers=headers)
    return response.status_code


@pytest.mark.asyncio
async def test_valid_bot_framework_token_is_processed_with_its_claims(client: AsyncClient, adapter: MagicMock):
    assert await _post(client, _token()) == 202
    assert adapter.claims_identity.is_authenticated
    assert adapter.claims_identity.get_claim_value("aud") == APP_ID


@pytest.mark.asyncio
async def test_tenant_issued_channel_token_is_processed(client: AsyncClient, adapter: MagicMock):
    assert await _post(client, _token(iss=f"https://login.microsoftonline.com/{TENANT_ID}/v2.0")) == 202


@pytest.mark.asyncio
async def test_unsigned_activity_is_rejected(client: AsyncClient, adapter: MagicMock):
    assert await _post(client, None) == 401
    adapter.process.assert_not_awaited()


@pytest.mark.asyncio
async def test_non_bearer_authorization_is_rejected(client: AsyncClient, adapter: MagicMock):
    response = await client.post(ROUTE, json=_activity(), headers={"Authorization": "Basic Zm9vOmJhcg=="})
    assert response.status_code == 401
    adapter.process.assert_not_awaited()


@pytest.mark.asyncio
async def test_unsigned_jwt_is_rejected(client: AsyncClient, adapter: MagicMock):
    unsigned = jwt.encode({"iss": BOT_FRAMEWORK_ISSUER, "aud": APP_ID, "serviceurl": SERVICE_URL}, None, "none")
    assert await _post(client, unsigned) == 401
    adapter.process.assert_not_awaited()


@pytest.mark.asyncio
async def test_garbage_token_is_rejected(client: AsyncClient, adapter: MagicMock):
    assert await _post(client, "not-a-jwt") == 401
    adapter.process.assert_not_awaited()


@pytest.mark.asyncio
async def test_wrongly_signed_token_is_rejected(client: AsyncClient, adapter: MagicMock):
    assert await _post(client, _token(private_key=BotFrameworkTokenFactory.FOREIGN_KEY)) == 401
    adapter.process.assert_not_awaited()


@pytest.mark.asyncio
async def test_expired_token_is_rejected(client: AsyncClient, adapter: MagicMock):
    expired = int(time.time()) - 3600
    assert await _post(client, _token(nbf=expired - 3600, exp=expired)) == 401
    adapter.process.assert_not_awaited()


@pytest.mark.asyncio
async def test_token_for_another_bot_is_rejected(client: AsyncClient, adapter: MagicMock):
    assert await _post(client, _token(aud="another-bot-app-id")) == 401
    adapter.process.assert_not_awaited()


@pytest.mark.asyncio
async def test_token_from_untrusted_issuer_is_rejected(client: AsyncClient, adapter: MagicMock):
    assert await _post(client, _token(iss="https://login.microsoftonline.com/other-tenant/v2.0")) == 401
    adapter.process.assert_not_awaited()


@pytest.mark.asyncio
async def test_token_issued_to_another_application_is_rejected(client: AsyncClient, adapter: MagicMock):
    other_app_token = _token(iss=f"https://login.microsoftonline.com/{TENANT_ID}/v2.0", ver="2.0", azp="other-app")
    assert await _post(client, other_app_token) == 401
    adapter.process.assert_not_awaited()


@pytest.mark.asyncio
async def test_activity_for_another_service_url_is_rejected(client: AsyncClient, adapter: MagicMock):
    assert await _post(client, _token(), _activity(service_url="https://attacker.example.com/")) == 401
    adapter.process.assert_not_awaited()


@pytest.mark.asyncio
async def test_token_without_service_url_is_rejected(client: AsyncClient, adapter: MagicMock):
    assert await _post(client, _token(serviceurl=None)) == 401
    adapter.process.assert_not_awaited()


@pytest.mark.asyncio
async def test_path_without_bot_configuration_is_not_found(
    client: AsyncClient, adapter: MagicMock, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(RoutesService, "get_credentials", MagicMock(return_value=None))
    assert await _post(client, _token()) == 404
    adapter.process.assert_not_awaited()


@pytest.mark.asyncio
async def test_signed_activity_reaches_the_bot_and_replies_to_the_token_service_url(
    client: AsyncClient, captured_responses: list
):
    response = await client.post(ROUTE, json=_activity(), headers={"Authorization": f"Bearer {_token()}"})

    assert response.is_success
    assert captured_responses[-1].payload["text"] == "pong"
    assert captured_responses[-1].payload["serviceUrl"] == SERVICE_URL
    assert captured_responses[-1].path == "/v3/conversations/conversation-1/activities"


@pytest.mark.asyncio
async def test_bot_in_the_loop_route_rejects_unsigned_replies_before_touching_the_handler(adapter: MagicMock):
    bot_in_the_loop_handler = BotInTheLoopHandler()
    configured_path = bot_in_the_loop_handler.path
    controller = BotInTheLoopController(auth=TestAuthHandler()).bot_in_the_loop_response()
    app = FastAPI()
    app.include_router(controller.router, prefix=f"/api/v1{controller.base_route}")
    app.dependency_overrides[use_nats] = lambda: MagicMock()
    app.dependency_overrides[use_external_agent_event_distributor] = lambda: MagicMock()
    app.dependency_overrides[BotInTheLoopHandler.use_bot_in_the_loop_handler] = lambda: bot_in_the_loop_handler
    signed_headers = {"Authorization": f"Bearer {_token()}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as bitl_client:
        unsigned = await bitl_client.post(f"{configured_path}?redirect=1", json=_activity())
        signed = await bitl_client.post(configured_path, json=_activity(), headers=signed_headers)

    assert unsigned.status_code == 401
    assert signed.status_code == 202
    assert bot_in_the_loop_handler.path == configured_path
    adapter.process.assert_awaited_once()
