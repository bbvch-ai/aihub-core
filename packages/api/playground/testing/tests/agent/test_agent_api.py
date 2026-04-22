import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from llama_index.core.base.llms.types import ChatMessage
from swiss_ai_hub.core.events.agent import UserMessageEvent
from swiss_ai_hub.core.infrastructure import enable_logging
from swiss_ai_hub.core.testing.auth_utils import TestAuthHandler

from swiss_ai_hub.api.routes.agent.agent_controller import AgentController
from swiss_ai_hub.api.runners.simulation.agent.simulated_agent_api_test_runner import SimulatedAgentApiTestRunner
from swiss_ai_hub.api.services.model_creation_service import ModelCreationService

AGENT_CLASS = "TestAgent"
AGENT_ID = "test_agent_1"

enable_logging()


@pytest_asyncio.fixture
async def agent_api_client():
    auth = TestAuthHandler()
    controller = AgentController(auth=auth).get_all_agent_instances().get_agent_instance()
    runner = SimulatedAgentApiTestRunner(agent_class=AGENT_CLASS, agent_id=AGENT_ID).with_simple_chunk_events()
    runner.mount(controller)
    await runner.start_simulation()
    app = runner.create_app()

    async with LifespanManager(app) as lifespan:
        runner.create_agent_config_in_db()

        async with AsyncClient(
            transport=ASGITransport(app=lifespan.app), base_url="http://test/api/v1/active"
        ) as client:
            yield client


@pytest.mark.asyncio
async def test_get_agent_instance(agent_api_client):
    """Test GET /agents/classes/{agent_class}/instances/{agent_id} returns correct agent details."""
    response = await agent_api_client.get(f"/agents/classes/{AGENT_CLASS}/instances/{AGENT_ID}")
    assert response.status_code == 200, f"Response: {response.text}"

    data = response.json()
    assert data.get("agent_class") == AGENT_CLASS
    assert data.get("agent_id") == AGENT_ID
    for key in ("agent_config", "start_events", "stop_events"):
        assert key in data


@pytest.mark.asyncio
async def test_get_all_agent_instances(agent_api_client):
    """Test GET /agents/instances returns a list containing the simulated agent."""
    response = await agent_api_client.get("/agents/instances")
    assert response.status_code == 200, f"Response: {response.text}"

    data = response.json()
    assert isinstance(data, list), "Response data should be a list"
    found = any(agent.get("agent_class") == AGENT_CLASS and agent.get("agent_id") == AGENT_ID for agent in data)
    assert found, "Simulated agent not found in agent instances"


@pytest.mark.asyncio
async def test_get_all_agent_instances_online_filter(agent_api_client):
    """Test GET /agents/instances?online=true returns online instances only."""
    response = await agent_api_client.get("/agents/instances?online=true")
    assert response.status_code == 200, f"Response: {response.text}"

    data = response.json()
    assert isinstance(data, list), "Response data should be a list"
    # All returned instances should be online
    for agent in data:
        assert agent.get("is_online") is True, f"Expected online agent, got: {agent}"


@pytest.mark.asyncio
async def test_send_event_to_agent(agent_api_client):
    """Test POST /agents/classes/{agent_class}/instances/{agent_id}/{event_name} returns a stop event.

    Note: The response model is based on StopEvent (not LLMStopEvent) because LLMStopEvent's
    complex Message type with ContentBlock unions causes schema parsing issues with Jambo.
    """
    user_message = ModelCreationService.create_input_model_from_event_class(UserMessageEvent)(
        agent_id=AGENT_ID, messages=[ChatMessage(role="user", content="Hey!")]
    )
    path = f"/agents/classes/{AGENT_CLASS}/instances/{AGENT_ID}/{UserMessageEvent.event_name_from_class()}"
    response = await agent_api_client.post(
        url=path,
        content=user_message.model_dump_json(),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200, f"Response: {response.text}"

    data = response.json()
    # Response should contain display fields from StopEvent
    assert data.get("display_name"), f"Expected display_name, got: {data}"
    assert data.get("display_description"), f"Expected display_description, got: {data}"
