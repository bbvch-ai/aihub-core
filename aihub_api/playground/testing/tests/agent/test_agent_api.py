import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import AsyncClient, ASGITransport

from aihub_api.runners.SimulatedAgentApiTestRunner import SimulatedAgentApiTestRunner
from aihub_api.routes.agent.AgentController import AgentController
from aihub_lib.auth.dependencies.NoAuthHandler.NoAuthHandler import NoAuthHandler


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def agent_api_client():
    agent_class = "test_agent"
    agent_id = "test_agent_1"
    auth = NoAuthHandler()  # This auth dependency returns a user that has access to all agents.
    controller = AgentController(auth=auth).discover_agents().get_agent()

    # Set up the simulated agent runner.
    runner = SimulatedAgentApiTestRunner(agent_class=agent_class, agent_id=agent_id).with_simple_chunk_events()
    runner.mount(controller)
    await runner.start_simulation()
    app = runner.get_app()

    async with LifespanManager(app) as lifespan:
        async with AsyncClient(
                transport=ASGITransport(app=lifespan.app), base_url="http://test/api/v1"
        ) as client:
            yield client


@pytest.mark.asyncio(loop_scope="module")
async def test_discover_agents(agent_api_client):
    """
    Test the GET /agent/discover endpoint.
    Expects the discovered agents list to include the simulated agent.
    """
    response = await agent_api_client.get("/agent/discover")
    assert response.status_code == 200, f"Response: {response.text}"

    data = response.json()
    # Expect a list of AgentDTO objects.
    assert isinstance(data, list), "Response data should be a list"

    # Check that our simulated agent is present.
    found = any(
        agent.get("agent_class") == "test_agent" and agent.get("agent_id") == "test_agent_1"
        for agent in data
    )
    assert found, "Simulated agent not found in discovered agents"


# -----------------------------------------------------------
# Test retrieving a specific agent when authorized.
# -----------------------------------------------------------
@pytest.mark.asyncio(loop_scope="module")
async def test_get_agent(agent_api_client):
    """
    Test the GET /agent/{agent_class}/{agent_id} endpoint with authorized access.
    Validates the returned AgentDTO structure.
    """
    response = await agent_api_client.get("/agent/test_agent/test_agent_1")
    assert response.status_code == 200, f"Response: {response.text}"

    data = response.json()
    # Validate basic structure.
    assert data.get("agent_class") == "test_agent"
    assert data.get("agent_id") == "test_agent_1"
    assert "agent_config" in data
    assert "start_events" in data
    assert "stop_events" in data

