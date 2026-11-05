from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from swiss_ai_hub.core.persistence.messaging.entities.thread_entity import AgentInstanceRef, ThreadEntity, User
from swiss_ai_hub.core.testing.auth_utils import TEST_USER_OID, TestAuthHandler

from swiss_ai_hub.api.routes.agent.agent_controller import AgentController
from swiss_ai_hub.api.runners.simulation.agent.simulated_agent_api_test_runner import SimulatedAgentApiTestRunner

AGENT_CLASS = "threads_listing_agent"
AGENT_ID = "threads_listing_agent_1"
OTHER_USER_ID = "someone-else"


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def api_client() -> AsyncGenerator[AsyncClient]:
    runner = SimulatedAgentApiTestRunner(agent_class=AGENT_CLASS, agent_id=AGENT_ID)
    runner.with_simple_chunk_events()
    runner.mount(AgentController(auth=TestAuthHandler()).get_agent_instance_threads())
    await runner.start_simulation()
    app = runner.create_app()
    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url="http://test") as client:
            yield client
    await runner.stop_simulation()


@pytest.mark.asyncio(loop_scope="module")
async def test_agent_admin_lists_only_their_own_threads(api_client: AsyncClient):
    """The test identity holds full admin access, yet another user's thread with the same agent stays hidden."""
    agent = AgentInstanceRef(agent_class=AGENT_CLASS, agent_id=AGENT_ID)
    own = ThreadEntity.create_thread("own", users=[User(user_id=TEST_USER_OID)], agents=[agent])
    others = ThreadEntity.create_thread("others", users=[User(user_id=OTHER_USER_ID)], agents=[agent])
    try:
        response = await api_client.get(f"/api/v1/active/agents/classes/{AGENT_CLASS}/instances/{AGENT_ID}/threads")
    finally:
        own.delete()
        others.delete()

    assert response.status_code == 200
    body = response.json()
    assert [thread["id"] for thread in body["threads"]] == [str(own.id)]
    assert body["total"] == 1
