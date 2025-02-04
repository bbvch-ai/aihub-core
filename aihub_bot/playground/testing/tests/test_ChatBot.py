import json
from typing import Dict

import httpx
import pytest_asyncio

from aihub_bot.routes.chat.ChatController import ChatController
from aihub_bot.routes.health.HealthController import HealthController
from aihub_bot.runners.SimulatedAgentBotTestRunner import SimulatedAgentBotTestRunner

PORT = 8001
API_PATH = "/api/v1"
AGENT_CLASS = "my_agent_class"
AGENT_ID = "my_agent_id"

HEALTH_ENDPOINT = f"http://localhost:{PORT}{API_PATH}/health/"
JSON_ENDPOINT = f"http://localhost:{PORT}{API_PATH}/chat/completions/{AGENT_CLASS}/{AGENT_ID}/json"
SERVICE_ENDPOINT = f"http://localhost:{PORT}/service"

CONVERSATION_ID = "test_conversation_id"
BOT_ID = "test_bot_id"
USER_ID = "test_user_id"
ACTIVITY_ID = "test_activity_id"

import asyncio
import pytest


async def start_api(runner: SimulatedAgentBotTestRunner):
    runner.with_simple_chunk_events()
    runner.mount(
        HealthController().get_health(),
        ChatController().completions_json(),
    )
    await runner.run()


# Fixture to start and stop the API server
@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def test_runner():
    runner = SimulatedAgentBotTestRunner(agent_class=AGENT_CLASS, agent_id=AGENT_ID)
    # Start the API server in a background task.
    server_task = asyncio.create_task(start_api(runner))

    # A simple way is to wait for the health endpoint to respond.
    async with httpx.AsyncClient() as client:
        for _ in range(10):  # Try for up to ~5 seconds
            try:
                response = await client.get(HEALTH_ENDPOINT)
                if response.status_code == 200:
                    break
            except httpx.RequestError:
                await asyncio.sleep(1)
        else:
            server_task.cancel()
            pytest.fail("API server did not start in time.")

    # Provide the base URL to the tests.
    yield runner

    # Teardown: cancel the API server task.
    server_task.cancel()
    try:
        await server_task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio(loop_scope="module")
async def test_update_conversation(test_runner: SimulatedAgentBotTestRunner):
    with open("conversation_update.json") as file:
        payload: Dict = json.loads(file.read())

    payload["serviceUrl"] = SERVICE_ENDPOINT
    payload["conversation"]["id"] = CONVERSATION_ID
    payload["from"]["id"] = USER_ID
    payload["recipient"]["id"] = BOT_ID

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url=JSON_ENDPOINT,
            json=payload,
        )

    assert response.status_code == 200
    assert test_runner.responses[-1].path == f"/v3/conversations/{CONVERSATION_ID}/activities"
    assert test_runner.responses[-1].payload["type"] == "message"
    assert test_runner.responses[-1].payload["conversation"]["id"] == CONVERSATION_ID
    assert test_runner.responses[-1].payload["from"]["id"] == BOT_ID
    assert test_runner.responses[-1].payload["recipient"]["id"] == USER_ID


@pytest.mark.asyncio(loop_scope="module")
async def test_send_message(test_runner: SimulatedAgentBotTestRunner):
    with open("user_message.json") as file:
        payload: Dict = json.loads(file.read())

    payload["serviceUrl"] = SERVICE_ENDPOINT
    payload["conversation"]["id"] = CONVERSATION_ID
    payload["from"]["id"] = USER_ID
    payload["recipient"]["id"] = BOT_ID
    payload["id"] = ACTIVITY_ID

    async with httpx.AsyncClient() as client:
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
