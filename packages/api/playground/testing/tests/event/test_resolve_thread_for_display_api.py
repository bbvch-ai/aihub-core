import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from bson import ObjectId
from httpx import ASGITransport, AsyncClient
from swiss_ai_hub.core.persistence.messaging.entities.persisted_agent_event_entity import PersistedAgentEventEntity
from swiss_ai_hub.core.persistence.messaging.entities.thread_entity import AgentInstanceRef, ThreadEntity, User
from swiss_ai_hub.core.testing.auth_utils import TestAuthHandler
from swiss_ai_hub.core.testing.auth_utils.test_identity import TEST_USER_OID
from swiss_ai_hub.core.topic_managers.agents.agent_topic_manager import AgentTopicManager

from swiss_ai_hub.api.routes.event.event_controller import EventController
from swiss_ai_hub.api.runners.api_test_runner import ApiTestRunner

EVENTS_BASE = "/api/v1/active/events"

pytestmark = pytest.mark.beanie


@pytest_asyncio.fixture(loop_scope="session")
async def api_client(beanie_test_database):
    runner = ApiTestRunner()
    auth = TestAuthHandler()
    runner.mount(EventController(auth=auth).resolve_thread_for_display())
    app = runner.create_app()
    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url="http://test") as client:
            yield client
        await ThreadEntity.delete_all()
        PersistedAgentEventEntity.objects.delete()


def _persist_display_event(thread_id: str, display_id: str, agent_id: str = "a1", run_id: str = "r1") -> None:
    PersistedAgentEventEntity(
        agent_class="TestAgent",
        agent_id=agent_id,
        thread_id=thread_id,
        display_id=display_id,
        run_id=run_id,
        event_id=str(ObjectId()),
        event_type=AgentTopicManager.DISPLAY_EVENT,
        event_name="ChunkEvent",
        event_data={"created_at": 1_730_000_000_000_000_000},
        event_parents=["ChunkEvent"],
    ).save()


async def test_resolves_thread_owned_by_user(api_client):
    thread_id = str(ObjectId())
    display_id = str(ObjectId())
    await ThreadEntity.create_thread(
        name="t",
        users=[User(user_id=TEST_USER_OID)],
        agents=[AgentInstanceRef(agent_id="a1", agent_class="TestAgent")],
        thread_id=ObjectId(thread_id),
    )
    _persist_display_event(thread_id, display_id)

    response = await api_client.get(f"{EVENTS_BASE}/agents/displays/{display_id}/thread")

    assert response.status_code == 200, response.text
    assert response.json()["thread_id"] == thread_id


async def test_returns_an_empty_thread_for_an_unowned_display(api_client):
    """Not an error: a plain-LLM turn owns no AI-Hub thread, and both callers treat that as normal."""
    response = await api_client.get(f"{EVENTS_BASE}/agents/displays/{str(ObjectId())}/thread")

    assert response.status_code == 200, response.text
    assert response.json()["thread_id"] == ""


# Note: the endpoint enforces thread access with the same guard as `get_agent_events_in_thread`
# (user-in-thread OR access-to-process). The fixed test identity has `aihub.admin.>`, so the 403
# branch is not reachable here — matching the sibling endpoint, which likewise has no 403 API test.


async def test_aitl_delegation_resolves_single_thread(api_client):
    thread_id = str(ObjectId())
    display_id = str(ObjectId())
    await ThreadEntity.create_thread(
        name="t",
        users=[User(user_id=TEST_USER_OID)],
        agents=[AgentInstanceRef(agent_id="namespace", agent_class="TestAgent")],
        thread_id=ObjectId(thread_id),
    )
    _persist_display_event(thread_id, display_id, agent_id="namespace", run_id="r1")
    _persist_display_event(thread_id, display_id, agent_id="rag", run_id="r2")

    response = await api_client.get(f"{EVENTS_BASE}/agents/displays/{display_id}/thread")

    assert response.status_code == 200, response.text
    assert response.json()["thread_id"] == thread_id
