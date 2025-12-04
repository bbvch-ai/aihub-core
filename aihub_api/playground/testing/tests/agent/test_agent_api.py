import pytest
import pytest_asyncio
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthHandler import (
    DangerousDevelopmentOnlyAuthHandler,
)
from aihub_lib.auth.identity.DangerousDevelopmentOnlyIdentityProvider.DangerousDevelopmentOnlyIdentityProvider import (
    DangerousDevelopmentOnlyIdentityProvider,
)
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.nats.events import UserMessageEvent
from aihub_lib.testing.auth_utils.role_mocks import mock_role_entity_methods  # noqa: F401
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from llama_index.core.base.llms.types import ChatMessage

from aihub_api.routes.agent.AgentController import AgentController
from aihub_api.routes.agent.AgentService import AgentService
from aihub_api.runners.simulation.agent.SimulatedAgentApiTestRunner import SimulatedAgentApiTestRunner
from aihub_api.services.ModelCreationService import ModelCreationService

AGENT_CLASS = "TestAgent"
AGENT_ID = "test_agent_1"

enable_logging()


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def agent_api_client():
    auth = DangerousDevelopmentOnlyAuthHandler(identity_provider=DangerousDevelopmentOnlyIdentityProvider())
    controller = AgentController(auth=auth).discover_agents().get_agents().get_agent()
    runner = SimulatedAgentApiTestRunner(agent_class=AGENT_CLASS, agent_id=AGENT_ID).with_simple_chunk_events()
    runner.mount(controller)
    await runner.start_simulation()
    app = runner.create_app()

    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url="http://test/api/v1") as client:
            yield client


@pytest.fixture(autouse=True)
def cleanup_db_and_cache():
    AgentService._clear_cache()
    yield
    AgentService._clear_cache()


@pytest.mark.asyncio(loop_scope="module")
async def test_discover_agents(agent_api_client):
    """Test GET /agent/discover returns a list containing the simulated agent."""
    response = await agent_api_client.get("/agents/discover")
    assert response.status_code == 200, f"Response: {response.text}"

    data = response.json()
    assert isinstance(data, list), "Response data should be a list"
    found = any(agent.get("agent_class") == AGENT_CLASS and agent.get("agent_id") == AGENT_ID for agent in data)
    assert found, "Simulated agent not found in discovered agents"


@pytest.mark.asyncio(loop_scope="module")
async def test_get_agent(agent_api_client):
    """Test GET /agent/{agent_class}/{agent_id} returns correct agent details."""
    response = await agent_api_client.get(f"/agents/{AGENT_CLASS}/{AGENT_ID}")
    assert response.status_code == 200, f"Response: {response.text}"

    data = response.json()
    assert data.get("agent_class") == AGENT_CLASS
    assert data.get("agent_id") == AGENT_ID
    for key in ("agent_config", "start_events", "stop_events"):
        assert key in data


@pytest.mark.asyncio(loop_scope="module")
async def test_send_event_to_agent(agent_api_client):
    """Test POST /agent/{agent_class}/{agent_id}/{event_name} returns correct agent details."""
    user_message = ModelCreationService.create_input_model_from_event_class(UserMessageEvent)(
        messages=[ChatMessage(role="user", content="Hey!")]
    )
    path = f"/agents/{AGENT_CLASS}/{AGENT_ID}/{UserMessageEvent.event_name_from_class()}"
    response = await agent_api_client.post(
        url=path,
        content=user_message.model_dump_json(),
    )
    assert response.status_code == 200, f"Response: {response.text}"

    data = response.json()
    assert data.get("output_messages")
    assert len(data.get("output_messages")) == 1
    assert data.get("output_messages")[0].get("role") == "assistant"
    assert data.get("output_messages")[0].get("contents")[0].get("text") == "First chunk.\nSecond chunk"
