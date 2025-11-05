import asyncio
import json
from pathlib import Path

import pytest
import pytest_asyncio
import requests
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthHandler import (
    DangerousDevelopmentOnlyAuthHandler,
)
from aihub_lib.auth.identity.DangerousDevelopmentOnlyIdentityProvider.DangerousDevelopmentOnlyIdentityProvider import (
    DangerousDevelopmentOnlyIdentityProvider,
)
from aihub_lib.routes.health.HealthController import HealthController
from aihub_lib.testing.logging.logger import enable_logging
from aihub_lib.testing.route_adapter.ASGIAdapter import ASGIAdapter
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from aihub_bot.routes.agent.AgentChatController import AgentChatController
from aihub_bot.runners.SimulatedAgentBotTestRunner import SimulatedAgentBotTestRunner

enable_logging()

BASE_URL = "http://test/api/v1"
PORT = 8001
AGENT_CLASS = "my_agent_class"
AGENT_ID = "my_agent_id"

JSON_ENDPOINT = f"{BASE_URL}/agent/chat/completions/{AGENT_CLASS}/{AGENT_ID}/json"
STREAM_ENDPOINT = f"{BASE_URL}/agent/chat/completions/{AGENT_CLASS}/{AGENT_ID}/stream"
SERVICE_ENDPOINT = f"{BASE_URL}/service"

CONVERSATION_ID = "test_conversation_id"
BOT_ID = "test_bot_id"
USER_ID = "test_user_id"
ACTIVITY_ID = "test_activity_id"


@pytest.fixture
def patch_requests_adapter(monkeypatch, test_runner):
    """Patch the request.Session to forward all calls made to the test domain to our fastapi application"""
    app = test_runner.create_app()
    original_session = requests.Session

    def session_factory(*args, **kwargs):
        session = original_session(*args, **kwargs)
        session.mount(BASE_URL, ASGIAdapter(app))
        return session

    monkeypatch.setattr(requests, "Session", session_factory)
    yield


@pytest.fixture
def patch_aiohttp_routing(monkeypatch, test_runner):
    """
    Patch aiohttp to route requests to the test app instead of making real network calls.

    ### What
    - Intercepts aiohttp requests and routes them to the FastAPI test app
    - Captures bot responses in test_runner.responses for assertion

    ### Why
    - The microsoft-agents SDK uses aiohttp (not requests) to send bot responses
    - Bot responses go to serviceUrl endpoints that need to reach BotTestRunner's /service handler
    - Without routing, responses don't get captured in test_runner.responses

    ### How
    - Patches aiohttp.ClientSession._request to use httpx.AsyncClient with ASGITransport
    - Routes requests to http://test/... and http://localhost:8001/... to the test app
    - Returns generic mocks for other URLs to prevent real network calls
    """
    try:
        import aiohttp
        from unittest.mock import AsyncMock
        from httpx import ASGITransport, AsyncClient

        app = test_runner.create_app()
        original_request = aiohttp.ClientSession._request

        async def routing_request(self, method, url, **kwargs):
            """Route requests to test app or return mock response."""
            str_url = str(url)

            # Check if this is a request to our test domain
            if str_url.startswith("http://test/") or str_url.startswith("http://localhost:8001/"):
                # Route to the test app using httpx
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    # Extract JSON data if present
                    json_data = kwargs.get("json")
                    data = kwargs.get("data")

                    # Make the request to the ASGI app
                    response = await client.request(
                        method=method, url=str_url, json=json_data, content=data, headers=kwargs.get("headers", {})
                    )

                    # Convert httpx response to aiohttp-like response
                    mock_response = AsyncMock()
                    mock_response.status = response.status_code
                    mock_response.reason = response.reason_phrase
                    mock_response.headers = dict(response.headers)
                    mock_response.text = AsyncMock(return_value=response.text)
                    mock_response.json = AsyncMock(return_value=response.json() if response.content else {})
                    mock_response.read = AsyncMock(return_value=response.content)
                    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
                    mock_response.__aexit__ = AsyncMock(return_value=None)

                    return mock_response
            else:
                # Generic mock for external URLs (e.g., Microsoft auth endpoints)
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.reason = "OK"
                mock_response.headers = {}
                mock_response.text = AsyncMock(return_value="{}")
                mock_response.json = AsyncMock(return_value={})
                mock_response.read = AsyncMock(return_value=b"{}")
                mock_response.__aenter__ = AsyncMock(return_value=mock_response)
                mock_response.__aexit__ = AsyncMock(return_value=None)
                return mock_response

        # Patch the _request method
        monkeypatch.setattr(aiohttp.ClientSession, "_request", routing_request)
    except ImportError:
        # If aiohttp isn't installed, skip this fixture
        pass
    yield


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def test_runner():
    runner = SimulatedAgentBotTestRunner(agent_class=AGENT_CLASS, agent_id=AGENT_ID)
    runner.with_simple_chunk_events()
    auth = DangerousDevelopmentOnlyAuthHandler(identity_provider=DangerousDevelopmentOnlyIdentityProvider())
    runner.mount(
        HealthController(auth=auth).get_health(), AgentChatController(auth=auth).completions_json().completions_stream()
    )
    await runner.start_simulation()
    return runner


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def client(test_runner: SimulatedAgentBotTestRunner):
    app = test_runner.create_app()
    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url=BASE_URL) as client:
            yield client


@pytest.mark.asyncio(loop_scope="module")
async def test_send_message(test_runner: SimulatedAgentBotTestRunner, client: AsyncClient, patch_aiohttp_routing):
    with open(Path(__file__).parent / "user_message.json") as file:
        payload: dict = json.loads(file.read())

    payload["serviceUrl"] = SERVICE_ENDPOINT
    payload["conversation"]["id"] = CONVERSATION_ID
    payload["from"]["id"] = USER_ID
    payload["recipient"]["id"] = BOT_ID
    payload["id"] = ACTIVITY_ID

    response = await client.post(
        url=JSON_ENDPOINT,
        json=payload,
    )

    assert response.status_code == 200
    assert test_runner.responses[-1].path == f"/v3/conversations/{CONVERSATION_ID}/activities/{ACTIVITY_ID}"
    assert test_runner.responses[-1].payload["type"] == "message"
    assert test_runner.responses[-1].payload["conversation"]["id"] == CONVERSATION_ID
    assert test_runner.responses[-1].payload["from"]["id"] == BOT_ID
    assert test_runner.responses[-1].payload["recipient"]["id"] == USER_ID
    assert test_runner.responses[-1].payload["text"] == "First chunk.\nSecond chunk."


@pytest.mark.asyncio(loop_scope="module")
async def test_stream_response(test_runner: SimulatedAgentBotTestRunner, client: AsyncClient, patch_aiohttp_routing):
    with open(Path(__file__).parent / "user_message.json") as file:
        payload: dict = json.loads(file.read())

    payload["serviceUrl"] = SERVICE_ENDPOINT
    payload["conversation"]["id"] = CONVERSATION_ID
    payload["from"]["id"] = USER_ID
    payload["recipient"]["id"] = BOT_ID
    payload["id"] = ACTIVITY_ID

    response = await client.post(
        url=STREAM_ENDPOINT,
        json=payload,
    )

    assert response.status_code == 200

    for _ in range(30):
        if (
            test_runner.responses[-1].payload["text"] == "First chunk.\nSecond chunk."
            and test_runner.responses[-2].payload["text"] == "First chunk.\n"
        ):
            break
        await asyncio.sleep(1)
    else:
        pytest.fail(f"Chunks not received in time. Last chunk: {test_runner.responses[-1].payload}")

    assert test_runner.responses[-2].path == f"/v3/conversations/{CONVERSATION_ID}/activities/{ACTIVITY_ID}"
    assert test_runner.responses[-2].payload["type"] == "message"
    assert test_runner.responses[-2].payload["conversation"]["id"] == CONVERSATION_ID
    assert test_runner.responses[-2].payload["from"]["id"] == BOT_ID
    assert test_runner.responses[-2].payload["recipient"]["id"] == USER_ID
    assert test_runner.responses[-2].payload["text"] == "First chunk.\n"

    assert test_runner.responses[-1].path.startswith(f"/v3/conversations/{CONVERSATION_ID}/activities/")
    assert test_runner.responses[-1].path != f"/v3/conversations/{CONVERSATION_ID}/activities/{ACTIVITY_ID}"
    assert test_runner.responses[-1].payload["conversation"]["id"] == CONVERSATION_ID
    assert test_runner.responses[-1].payload["from"]["id"] == BOT_ID
    assert test_runner.responses[-1].payload["recipient"]["id"] == USER_ID
    assert test_runner.responses[-1].payload["text"] == "First chunk.\nSecond chunk."
