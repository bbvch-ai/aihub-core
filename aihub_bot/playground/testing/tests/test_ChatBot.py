import asyncio
import json
from pathlib import Path

import pytest
import pytest_asyncio
import requests
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthHandler import (
    DangerousDevelopmentOnlyAuthHandler,
)
from aihub_lib.infrastructure.api.AIHubSettings import AIHubSettings
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.infrastructure.mongo.MongoSettings import MongoSettings
from aihub_lib.routes.health.HealthController import HealthController
from aihub_lib.testing.route_adapter.ASGIAdapter import ASGIAdapter
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from mongoengine import connect, disconnect

from aihub_bot.persistence.entities.ConversationEntity import ConversationEntity
from aihub_bot.persistence.entities.PathEntity import Credentials, PathEntity
from aihub_lib.persistence.messaging.entities.ThreadEntity import ThreadEntity
from aihub_lib.persistence.utils import str_to_object_id
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


@pytest.fixture(scope="module")
def setup_test_credentials():
    """Set up PathEntity credentials for test endpoints"""
    # Connect to MongoDB
    connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
        uuidRepresentation="standard",
    )

    # Create credentials for JSON endpoint
    json_path = f"/api/v1/agent/chat/completions/{AGENT_CLASS}/{AGENT_ID}/json"
    stream_path = f"/api/v1/agent/chat/completions/{AGENT_CLASS}/{AGENT_ID}/stream"

    # Clean up any existing test credentials
    PathEntity.objects(path=json_path).delete()
    PathEntity.objects(path=stream_path).delete()

    # Create test credentials
    test_credentials = Credentials(
        APP_TYPE="MultiTenant", APP_ID="test_app_id", APP_PASSWORD="test_app_password", APP_TENANTID="test_tenant_id"
    )

    # Create PathEntity records for both endpoints
    PathEntity(path=json_path, credentials=test_credentials, system_message="Test system message").save()
    PathEntity(path=stream_path, credentials=test_credentials, system_message="Test system message").save()

    yield

    # Clean up test data
    try:
        PathEntity.objects(path=json_path).delete()
        PathEntity.objects(path=stream_path).delete()
    except Exception:
        # Connection may already be closed, ignore cleanup errors
        pass
    finally:
        try:
            disconnect()
        except Exception:
            pass


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


@pytest.fixture(autouse=True)
def cleanup_conversation():
    """Clean up conversation and thread state before each test."""
    thread_id = str(str_to_object_id(CONVERSATION_ID))
    # Clean up before test (connection may not exist yet)
    try:
        ConversationEntity.objects(conversation_id=CONVERSATION_ID).delete()
        ThreadEntity.objects(id=thread_id).delete()
    except Exception:
        pass
    yield
    # Clean up after test (connection may be closed)
    try:
        ConversationEntity.objects(conversation_id=CONVERSATION_ID).delete()
        ThreadEntity.objects(id=thread_id).delete()
    except Exception:
        pass


@pytest_asyncio.fixture(scope="function")
async def test_runner(captured_responses):
    runner = SimulatedAgentBotTestRunner(agent_class=AGENT_CLASS, agent_id=AGENT_ID)
    runner.with_simple_chunk_events()
    runner.responses = captured_responses  # Wire captured responses to test_runner
    auth = DangerousDevelopmentOnlyAuthHandler()
    runner.mount(
        HealthController(auth=auth).get_health(), AgentChatController(auth=auth).completions_json().completions_stream()
    )
    await runner.start_simulation()
    return runner


@pytest_asyncio.fixture(scope="function")
async def client(test_runner: SimulatedAgentBotTestRunner):
    app = test_runner.create_app()
    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url=BASE_URL) as client:
            yield client


@pytest.mark.asyncio
async def test_send_message(
    test_runner: SimulatedAgentBotTestRunner, client: AsyncClient, patch_requests_adapter, setup_test_credentials
):
    with open(Path(__file__).parent / "user_message.json") as file:
        payload: dict = json.loads(file.read())

    payload["serviceUrl"] = SERVICE_ENDPOINT
    payload["conversation"]["id"] = CONVERSATION_ID
    payload["from"]["id"] = USER_ID
    payload["recipient"]["id"] = BOT_ID
    payload["id"] = ACTIVITY_ID
    payload["channelId"] = "emulator"  # Required by Bot Framework

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


@pytest.mark.flaky
@pytest.mark.asyncio
async def test_stream_response(
    test_runner: SimulatedAgentBotTestRunner, client: AsyncClient, patch_requests_adapter, setup_test_credentials
):
    with open(Path(__file__).parent / "user_message.json") as file:
        payload: dict = json.loads(file.read())

    payload["serviceUrl"] = SERVICE_ENDPOINT
    payload["conversation"]["id"] = CONVERSATION_ID
    payload["from"]["id"] = USER_ID
    payload["recipient"]["id"] = BOT_ID
    payload["id"] = ACTIVITY_ID
    payload["channelId"] = "emulator"  # Required by Bot Framework

    response = await client.post(
        url=STREAM_ENDPOINT,
        json=payload,
    )

    assert response.status_code == 200

    # Wait a bit for streaming to complete
    await asyncio.sleep(2)

    # Debug: Show what we captured
    print(f"\n\nCaptured {len(test_runner.responses)} responses:")
    for i, resp in enumerate(test_runner.responses):
        print(f"  Response {i}: path={resp.path}, text={resp.payload.get('text', 'N/A')}")

    for _ in range(60):
        if len(test_runner.responses) >= 2:
            if test_runner.responses[-1].payload["text"] == "First chunk.\nSecond chunk.":
                break
        await asyncio.sleep(1)
    else:
        last_response = test_runner.responses[-1].payload if test_runner.responses else "NONE"
        pytest.fail(f"Chunks not received in time. Got {len(test_runner.responses)} responses. Last: {last_response}")

    assert test_runner.responses[-1].path.startswith(f"/v3/conversations/{CONVERSATION_ID}/activities/")
    assert test_runner.responses[-1].path != f"/v3/conversations/{CONVERSATION_ID}/activities/{ACTIVITY_ID}"
    assert test_runner.responses[-1].payload["conversation"]["id"] == CONVERSATION_ID
    assert test_runner.responses[-1].payload["from"]["id"] == BOT_ID
    assert test_runner.responses[-1].payload["recipient"]["id"] == USER_ID
    assert test_runner.responses[-1].payload["text"] == "First chunk.\nSecond chunk."
