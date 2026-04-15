import json

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.persistence.agents.agent_config_entity_document import AgentConfigEntityDocument
from swiss_ai_hub.core.testing.auth_utils import TestAuthHandler

from swiss_ai_hub.api.routes.openai.openai_controller import OpenaiController
from swiss_ai_hub.api.runners.simulation.agent.simulated_agent_api_test_runner import SimulatedAgentApiTestRunner

AGENT_CLASS = "test_agent"
AGENT_ID = "test_agent_1"
BASE_URL = "http://test/api/v1/active"
MODELS_ENDPOINT = "/openai/models"
COMPLETIONS_ENDPOINT = "/openai/chat/completions"


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def api_client():
    auth = TestAuthHandler()
    controller = (
        OpenaiController(auth=auth)
        .get_models_with_assistants()
        .get_model_with_assistants()
        .chat_completion_with_assistants()
    )
    runner = SimulatedAgentApiTestRunner(agent_class=AGENT_CLASS, agent_id=AGENT_ID).with_simple_chunk_events()
    runner.mount(controller)
    await runner.start_simulation()
    app = runner.create_app()
    async with LifespanManager(app) as lifespan:
        # Create agent config in database after DB connection is established
        runner.create_agent_config_in_db()
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url=BASE_URL) as client:
            yield client


@pytest.mark.asyncio(loop_scope="module")
async def test_get_models(api_client):
    """Test GET /openai/models returns a valid model list."""
    response = await api_client.get(MODELS_ENDPOINT)
    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()
    assert data.get("object") == "list"
    assert isinstance(data.get("data"), list)
    model_ids = [model.get("id") for model in data.get("data")]
    assert f"{AGENT_CLASS}/{AGENT_ID}" in model_ids


@pytest.mark.asyncio(loop_scope="module")
async def test_get_model(api_client):
    """Test GET /openai/models/{full_path} returns valid model details."""
    response = await api_client.get(f"{MODELS_ENDPOINT}/{AGENT_CLASS}/{AGENT_ID}")
    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()
    assert data.get("id") == f"{AGENT_CLASS}/{AGENT_ID}"
    assert data.get("object") == "assistant"
    assert isinstance(data.get("created"), int)
    assert data.get("owned_by") == "aihub"


@pytest.mark.asyncio(loop_scope="module")
async def test_chat_completions_stream(api_client):
    """Test streaming chat completions endpoint returns expected chunks."""
    payload = {
        "model": f"{AGENT_CLASS}/{AGENT_ID}",
        "messages": [{"role": "user", "content": "Hello!"}],
        "stream": True,
    }
    response = await api_client.post(COMPLETIONS_ENDPOINT, json=payload)
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
        assert delta.get("content") == expected_content[index], (
            f"Expected message content '{expected_content[index]}' but got '{delta.get('content')}'"
        )
        assert delta.get("role") == "assistant", f"Expected role 'assistant' but got '{delta.get('role')}'"


@pytest.mark.asyncio(loop_scope="module")
async def test_chat_completions_json(api_client):
    """Test JSON chat completions endpoint returns expected combined message."""
    payload = {
        "model": f"{AGENT_CLASS}/{AGENT_ID}",
        "messages": [{"role": "user", "content": "Hello!"}],
        "stream": False,
    }
    response = await api_client.post(COMPLETIONS_ENDPOINT, json=payload)
    assert response.status_code == 200, f"Response: {response.text}"

    data = response.json()

    assert data.get("object") == "chat.completion", f"Unexpected object type: {data.get('object')}"
    choices = data.get("choices", [])
    assert choices, "No choices returned in the response"
    message = choices[0].get("message", {})
    expected = "First chunk.\nSecond chunk"
    assert message.get("content") == expected, (
        f"Expected message content '{expected}' but got '{message.get('content')}'"
    )


@pytest.mark.asyncio(loop_scope="module")
async def test_chat_completions_json_with_custom_agent_config(api_client):
    """Test JSON chat completions with custom agent config."""
    AgentConfigEntityDocument.delete_if_exists_for_class_and_id(agent_class=AGENT_CLASS, agent_id=AGENT_ID)
    custom_agent_config = AgentConfig(
        agent_id=AGENT_ID,
        name=LocaleString(en="Override Test Agent"),
        description=LocaleString(en="This is a test agent with custom config."),
    )
    custom_agent_config_entity = AgentConfigEntityDocument.from_agent_config(custom_agent_config, AGENT_CLASS)
    custom_agent_config_entity.save()
    payload = {
        "model": f"{AGENT_CLASS}/{AGENT_ID}",
        "messages": [{"role": "user", "content": "Hello!"}],
        "stream": False,
    }
    response = await api_client.post(COMPLETIONS_ENDPOINT, json=payload)
    custom_agent_config_entity.delete()

    assert response.status_code == 200, f"Response: {response.text}"

    data = response.json()
    assert data.get("object") == "chat.completion", f"Unexpected object type: {data.get('object')}"
    choices = data.get("choices", [])
    assert choices, "No choices returned in the response"
    message = choices[0].get("message", {})
    expected = "First chunk.\nSecond chunk"
    assert message.get("content") == expected, (
        f"Expected message content '{expected}' but got '{message.get('content')}'"
    )
