import pytest
import pytest_asyncio
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthHandler import (
    DangerousDevelopmentOnlyAuthHandler,
)
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.nats.events.discovery.EventSpecs import EventSpecs
from aihub_lib.testing.auth_utils.role_mocks import mock_role_entity_methods  # noqa: F401
from aihub_lib.testing.auth_utils.tenant_mocks import mock_tenant_entity_autouse  # noqa: F401
from aihub_lib.testing.auth_utils.user_mocks import mock_user_entity_autouse  # noqa: F401
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from aihub_api.routes.agent.AgentController import AgentController
from aihub_api.runners.simulation.agent.SimulatedAgentApiTestRunner import SimulatedAgentApiTestRunner
from aihub_api.services.ModelCreationService import ModelCreationService
from playground.testing.tests.agent.events.TestStartEvent import TestStartEvent
from playground.testing.tests.agent.events.TestStopEvent import TestStopEvent

AGENT_CLASS = "TestAgent"
AGENT_ID = "test_agent_1"
TEST_START_EVENT = TestStartEvent.event_name_from_class()
START_EVENT_SPECS = EventSpecs.from_event_class(TestStartEvent)
STOP_EVENT_SPECS = EventSpecs.from_event_class(TestStopEvent)


enable_logging()


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def agent_api_client():
    auth = DangerousDevelopmentOnlyAuthHandler()
    controller = AgentController(auth=auth).get_all_agent_instances().get_agent_instance()
    runner = SimulatedAgentApiTestRunner(
        agent_class=AGENT_CLASS,
        agent_id=AGENT_ID,
        start_events=[START_EVENT_SPECS],
        stop_events=[STOP_EVENT_SPECS],
    )
    runner.simulated_events = [
        TestStopEvent(payload="Das ist ein test."),
    ]  # Simulated event for testing
    runner.mount(controller)
    await runner.start_simulation()
    app = runner.create_app()

    async with LifespanManager(app) as lifespan:
        # Create agent config in database after lifespan starts (database is now connected)
        runner.create_agent_config_in_db()
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url="http://test/api/v1") as client:
            yield client


@pytest.fixture(autouse=True)
def cleanup_db_and_cache():
    yield


@pytest.mark.asyncio(loop_scope="module")
async def test_get_all_agent_instances(agent_api_client):
    """Test GET /agents/instances returns a list containing the simulated agent."""
    response = await agent_api_client.get("/agents/instances")
    assert response.status_code == 200, f"Response: {response.text}"

    data = response.json()
    assert isinstance(data, list), "Response data should be a list"
    found = any(agent.get("agent_class") == AGENT_CLASS and agent.get("agent_id") == AGENT_ID for agent in data)
    assert found, "Simulated agent not found in agent instances"


@pytest.mark.asyncio(loop_scope="module")
async def test_get_agent_instance(agent_api_client):
    """Test GET /agents/classes/{agent_class}/instances/{agent_id} returns correct agent details."""
    response = await agent_api_client.get(f"/agents/classes/{AGENT_CLASS}/instances/{AGENT_ID}")
    assert response.status_code == 200, f"Response: {response.text}"

    data = response.json()
    assert data.get("agent_class") == AGENT_CLASS
    assert data.get("agent_id") == AGENT_ID
    for key in ("agent_config", "start_events", "stop_events"):
        assert key in data

    assert len(data.get("start_events")) == 1
    assert data.get("start_events")[0].get("event_name") == START_EVENT_SPECS.event_name
    assert data.get("start_events")[0].get("event_schema") == START_EVENT_SPECS.event_schema
    assert data.get("start_events")[0].get("event_parents") == START_EVENT_SPECS.event_parents
    assert len(data.get("stop_events")) == 1
    assert data.get("stop_events")[0].get("event_name") == STOP_EVENT_SPECS.event_name
    assert data.get("stop_events")[0].get("event_schema") == STOP_EVENT_SPECS.event_schema
    assert data.get("stop_events")[0].get("event_parents") == STOP_EVENT_SPECS.event_parents


@pytest.mark.asyncio(loop_scope="module")
async def test_send_event_to_agent(agent_api_client):
    """Test POST /agents/classes/{agent_class}/instances/{agent_id}/{event_name} returns correct agent details."""
    start_event_input = ModelCreationService.create_input_model_from_event_class(TestStartEvent)(
        agent_id=AGENT_ID,
        payload="Das ist ein test.",
    )
    path = f"/agents/classes/{AGENT_CLASS}/instances/{AGENT_ID}/{TEST_START_EVENT}"
    response = await agent_api_client.post(
        url=path,
        content=start_event_input.model_dump_json(),
    )
    assert response.status_code == 200, f"Response: {response.text}"

    data = response.json()
    assert data.get("payload") == "Das ist ein test."
