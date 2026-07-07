import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from bson import ObjectId
from httpx import ASGITransport, AsyncClient
from swiss_ai_hub.core.events.agent import ChunkEvent, LLMStopEvent, Message
from swiss_ai_hub.core.testing.auth_utils import TestAuthHandler

from swiss_ai_hub.api.routes.openai.openai_controller import OpenaiController
from swiss_ai_hub.api.runners.simulation.agent.simulated_agent_api_test_runner import SimulatedAgentApiTestRunner

BASE_URL = "http://test/api/v1/active"
COMPLETIONS_ENDPOINT = "/openai/chat/completions"

AGENT_X_CLASS, AGENT_X_ID, AGENT_X_TEXT = "agent_x", "agent_x_1", "Response from agent X"
AGENT_Y_CLASS, AGENT_Y_ID, AGENT_Y_TEXT = "agent_y", "agent_y_1", "Response from agent Y"


def _runner_with_text(agent_class: str, agent_id: str, text: str) -> SimulatedAgentApiTestRunner:
    runner = SimulatedAgentApiTestRunner(agent_class=agent_class, agent_id=agent_id)
    runner.simulated_events = [
        ChunkEvent(content=text, model_name="sim"),
        LLMStopEvent(output_messages=[Message.from_string(role="assistant", content=text)]),
    ]
    return runner


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def api_client():
    auth = TestAuthHandler()
    controller = OpenaiController(auth=auth).get_models_with_assistants().chat_completion_with_assistants()

    runner_x = _runner_with_text(AGENT_X_CLASS, AGENT_X_ID, AGENT_X_TEXT)
    runner_x.mount(controller)
    await runner_x.start_simulation()

    runner_y = _runner_with_text(AGENT_Y_CLASS, AGENT_Y_ID, AGENT_Y_TEXT)
    await runner_y.start_simulation()

    app = runner_x.create_app()
    async with LifespanManager(app) as lifespan:
        runner_x.create_agent_config_in_db()
        runner_y.create_agent_config_in_db()
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url=BASE_URL) as client:
            yield client


async def _completion_content(client: AsyncClient, model: str, thread_id: str) -> str:
    response = await client.post(
        COMPLETIONS_ENDPOINT,
        json={
            "model": model,
            "messages": [{"role": "user", "content": "Hello!"}],
            "stream": False,
            "metadata": {"thread_id": thread_id, "display_id": str(ObjectId())},
        },
    )
    assert response.status_code == 200, f"Response: {response.text}"
    return response.json()["choices"][0]["message"]["content"]


@pytest.mark.asyncio(loop_scope="module")
async def test_two_agents_in_one_thread_route_to_their_own_agent(api_client):
    """Reproduction of #1283: two different agents selected within one chat (shared thread_id) must each
    produce their own answer, not both the first agent's."""
    shared_thread_id = str(ObjectId())

    content_x = await _completion_content(api_client, f"{AGENT_X_CLASS}/{AGENT_X_ID}", shared_thread_id)
    content_y = await _completion_content(api_client, f"{AGENT_Y_CLASS}/{AGENT_Y_ID}", shared_thread_id)

    assert AGENT_X_TEXT in content_x
    assert AGENT_Y_TEXT not in content_x
    assert AGENT_Y_TEXT in content_y
    assert AGENT_X_TEXT not in content_y
