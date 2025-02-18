import json
import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import AsyncClient, ASGITransport

from aihub_api.runners.SimulatedAgentApiTestRunner import SimulatedAgentApiTestRunner
from aihub_api.routes.chat.ChatController import ChatController
from aihub_lib.auth.dependencies.NoAuthHandler.NoAuthHandler import NoAuthHandler

AGENT_CLASS = "test_agent"
AGENT_ID = "test_agent_1"
BASE_URL = "http://test/api/v1"


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def chat_api_client():
    auth = NoAuthHandler()
    controller = ChatController(auth=auth).completions_stream().completions_json()
    runner = SimulatedAgentApiTestRunner(agent_class=AGENT_CLASS, agent_id=AGENT_ID).with_simple_chunk_events()
    runner.mount(controller)
    await runner.start_simulation()
    app = runner.get_app()
    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url=BASE_URL) as client:
            yield client


@pytest.mark.asyncio(loop_scope="module")
async def test_chat_completions_stream(chat_api_client):
    """Test streaming chat completions endpoint returns expected chunks."""
    payload = {"messages": [{"role": "user", "content": "Hello!"}]}
    response = await chat_api_client.post(f"/chat/completions/{AGENT_CLASS}/{AGENT_ID}/stream", json=payload)
    assert response.status_code == 200, f"Response: {response.text}"

    chunk_aggregate = ""
    async for chunk in response.aiter_text():
        chunk_aggregate += chunk

    data_lines = [line for line in chunk_aggregate.split("\n") if line]
    data_jsons = [json.loads(line.strip()[len("data: ") :]) for line in data_lines]

    expected_content = ["First chunk.\n", "Second chunk", ""]
    for index, data in enumerate(data_jsons):
        assert data.get("object") == "chat.completion.chunk", f"Unexpected object type: {data.get('object')}"
        assert data.get("choices"), "No choices returned in the response"
        delta = data.get("choices")[0].get("delta", {})
        assert (
            delta.get("content") == expected_content[index]
        ), f"Expected message content '{expected_content[index]}' but got '{delta.get('content')}'"
        assert delta.get("role") == "assistant", f"Expected role 'assistant' but got '{delta.get('role')}'"


@pytest.mark.asyncio(loop_scope="module")
async def test_chat_completions_json(chat_api_client):
    """Test JSON chat completions endpoint returns expected combined message."""
    payload = {"messages": [{"role": "user", "content": "Hello!"}]}
    response = await chat_api_client.post(f"/chat/completions/{AGENT_CLASS}/{AGENT_ID}/json", json=payload)
    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()

    assert data.get("object") == "chat.completion", f"Unexpected object type: {data.get('object')}"
    choices = data.get("choices", [])
    assert choices, "No choices returned in the response"
    message = choices[0].get("message", {})
    expected = "First chunk.\nSecond chunk"
    assert (
        message.get("content") == expected
    ), f"Expected message content '{expected}' but got '{message.get('content')}'"
