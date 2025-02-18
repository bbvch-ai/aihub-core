import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import AsyncClient, ASGITransport

from aihub_api.runners.SimulatedAgentApiTestRunner import SimulatedAgentApiTestRunner
from aihub_api.routes.agent.AgentController import AgentController
from aihub_lib.auth.dependencies.NoAuthHandler.NoAuthHandler import NoAuthHandler

AGENT_CLASS = "test_agent"
AGENT_ID = "test_agent_1"


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def agent_api_client():
    auth = NoAuthHandler()
    controller = AgentController(auth=auth).discover_agents().get_agent()
    runner = SimulatedAgentApiTestRunner(agent_class=AGENT_CLASS, agent_id=AGENT_ID).with_simple_chunk_events()
    runner.mount(controller)
    await runner.start_simulation()
    app = runner.get_app()

    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url="http://test/api/v1") as client:
            yield client


@pytest.mark.asyncio(loop_scope="module")
async def test_discover_agents(agent_api_client):
    """Test GET /agent/discover returns a list containing the simulated agent."""
    response = await agent_api_client.get("/agent/discover")
    assert response.status_code == 200, f"Response: {response.text}"

    data = response.json()
    assert isinstance(data, list), "Response data should be a list"
    found = any(agent.get("agent_class") == AGENT_CLASS and agent.get("agent_id") == AGENT_ID for agent in data)
    assert found, "Simulated agent not found in discovered agents"


@pytest.mark.asyncio(loop_scope="module")
async def test_get_agent(agent_api_client):
    """Test GET /agent/{agent_class}/{agent_id} returns correct agent details."""
    response = await agent_api_client.get(f"/agent/{AGENT_CLASS}/{AGENT_ID}")
    assert response.status_code == 200, f"Response: {response.text}"

    data = response.json()
    assert data.get("agent_class") == AGENT_CLASS
    assert data.get("agent_id") == AGENT_ID
    for key in ("agent_config", "start_events", "stop_events"):
        assert key in data
