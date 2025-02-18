import json

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import AsyncClient, ASGITransport

from aihub_api.runners.SimulatedAgentApiTestRunner import SimulatedAgentApiTestRunner
from aihub_api.routes.chat.ChatController import ChatController
from aihub_lib.auth.dependencies.NoAuthHandler.NoAuthHandler import NoAuthHandler


# Fixture for setting up the ChatController endpoints with simulation.
@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def chat_api_client():
    agent_class = "test_agent"
    agent_id = "test_agent_1"
    auth = NoAuthHandler()
    # Create a ChatController instance with both streaming and JSON endpoints.
    controller = ChatController(auth=auth).completions_stream().completions_json()
    # Set up the simulated agent with simple chunk events (which produce "First chunk.\n" and "Second chunk")
    runner = SimulatedAgentApiTestRunner(agent_class=agent_class, agent_id=agent_id).with_simple_chunk_events()
    runner.mount(controller)
    await runner.start_simulation()
    app = runner.get_app()

    # All endpoints are mounted under /api/v1
    async with LifespanManager(app) as lifespan:
        async with AsyncClient(
                transport=ASGITransport(app=lifespan.app),
                base_url="http://test/api/v1"
        ) as client:
            yield client


@pytest.mark.asyncio(loop_scope="module")
async def test_chat_completions_stream(chat_api_client):
    """
    Test the streaming chat completions endpoint.
    Expects the SSE stream to eventually yield a combined message:
    "First chunk.\nSecond chunk"
    """
    payload = {
        "messages": [
            {"role": "user", "content": "Hello!"}
        ]
    }
    # The endpoint is mounted at /api/v1/chat/completions/{agent_class}/{agent_id}/stream
    response = await chat_api_client.post("/chat/completions/test_agent/test_agent_1/stream", json=payload)
    assert response.status_code == 200, f"Response: {response.text}"

    # Collect streaming response text.
    chunk_aggregate = ""
    async for chunk in response.aiter_text():
        chunk_aggregate += chunk

    data_lines = chunk_aggregate.split("\n")
    data_lines = [line for line in data_lines if line]
    data_jsons = [json.loads(line.strip()[len("data: "):]) for line in data_lines]

    print(data_jsons)

    assert len(data_jsons) == 3, "No chunks received in the stream"

    expected_content = [
        "First chunk.\n",
        "Second chunk",
        ""
    ]
    for index, data in enumerate(data_jsons):
        assert data.get("object") == "chat.completion.chunk", f"Unexpected object type: {data.get('object')}"
        assert data.get("choices"), "No choices returned in the response"
        delta = data.get("choices")[0].get("delta", {})
        assert delta.get("content") == expected_content[index], f"Expected message content '{expected_content[index]}' but got '{delta.get('content')}'"
        assert delta.get("role") == "assistant", f"Expected role 'agent' but got '{delta.get('role')}'"

@pytest.mark.asyncio(loop_scope="module")
async def test_chat_completions_json(chat_api_client):
    """
    Test the JSON chat completions endpoint.
    Verifies that the returned JSON response contains the expected message text.
    """
    payload = {
        "messages": [
            {"role": "user", "content": "Hello!"}
        ]
    }
    # The endpoint is mounted at /api/v1/chat/completions/{agent_class}/{agent_id}/json
    response = await chat_api_client.post("/chat/completions/test_agent/test_agent_1/json", json=payload)
    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()

    # Validate the structure and contents of the ChatCompletionsSuccessResponse.
    # In particular, the response should include our combined message.
    assert data.get("object") == "chat.completion", f"Unexpected object type: {data.get('object')}"
    choices = data.get("choices", [])
    assert choices, "No choices returned in the response"
    message = choices[0].get("message", {})
    expected = "First chunk.\nSecond chunk"
    assert message.get(
        "content") == expected, f"Expected message content '{expected}' but got '{message.get('content')}'"
