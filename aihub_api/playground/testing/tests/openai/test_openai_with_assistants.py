import json

import pytest
import pytest_asyncio
from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthHandler import (
    DangerousDevelopmentOnlyAuthHandler,
)
from aihub_lib.auth.identity.DangerousDevelopmentOnlyIdentityProvider.DangerousDevelopmentOnlyIdentityProvider import (
    DangerousDevelopmentOnlyIdentityProvider,
)
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.persistence.agents.AgentConfigEntityDocument import AgentConfigEntityDocument
from aihub_lib.testing.auth_utils.role_mocks import mock_role_entity_admin_only  # noqa: F401
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from aihub_api.routes.openai.OpenaiController import OpenaiController
from aihub_api.runners.simulation.agent.SimulatedAgentApiTestRunner import SimulatedAgentApiTestRunner

AGENT_CLASS = "test_agent"
AGENT_ID = "test_agent_1"
BASE_URL = "http://test/api/v1"
MODELS_ENDPOINT = "/openai/models"
COMPLETIONS_ENDPOINT = "/openai/chat/completions"


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def api_client():
    auth = DangerousDevelopmentOnlyAuthHandler(identity_provider=DangerousDevelopmentOnlyIdentityProvider())
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
        assert (
            delta.get("content") == expected_content[index]
        ), f"Expected message content '{expected_content[index]}' but got '{delta.get('content')}'"
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
    assert (
        message.get("content") == expected
    ), f"Expected message content '{expected}' but got '{message.get('content')}'"


@pytest.mark.asyncio(loop_scope="module")
async def test_chat_completions_json_with_custom_agent_config(api_client):
    """Test JSON chat completions with custom agent config."""
    AgentConfigEntityDocument.delete_if_exists_for_class_and_id(agent_class=AGENT_CLASS, agent_id=AGENT_ID)
    custom_agent_config = AgentConfig(
        agent_id=AGENT_ID,
        agent_class=AGENT_CLASS,
        name=LocaleString(en="Override Test Agent"),
        description=LocaleString(en="This is a test agent with custom config."),
    )
    custom_agent_config_entity = AgentConfigEntityDocument.from_agent_config(custom_agent_config)
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
    assert (
        message.get("content") == expected
    ), f"Expected message content '{expected}' but got '{message.get('content')}'"
