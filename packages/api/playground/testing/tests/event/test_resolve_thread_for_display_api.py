import pytest
from bson import ObjectId
from fastapi.testclient import TestClient
from mongoengine import connect, disconnect
from swiss_ai_hub.core.infrastructure import AIHubSettings, MongoSettings
from swiss_ai_hub.core.persistence.messaging.entities.persisted_agent_event_entity import PersistedAgentEventEntity
from swiss_ai_hub.core.persistence.messaging.entities.thread_entity import AgentInstanceRef, ThreadEntity, User
from swiss_ai_hub.core.testing.auth_utils import TestAuthHandler
from swiss_ai_hub.core.testing.auth_utils.test_identity import TEST_USER_OID
from swiss_ai_hub.core.topic_managers.agents.agent_topic_manager import AgentTopicManager

from swiss_ai_hub.api.routes.event.event_controller import EventController
from swiss_ai_hub.api.runners.api_test_runner import ApiTestRunner

EVENTS_BASE = "/api/v1/active/events"


@pytest.fixture(scope="function")
def mongodb():
    yield
    connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
        uuidRepresentation="standard",
    )
    ThreadEntity.objects.delete()
    PersistedAgentEventEntity.objects.delete()
    disconnect()


@pytest.fixture
def api_client(mongodb):
    runner = ApiTestRunner()
    auth = TestAuthHandler()
    runner.mount(EventController(auth=auth).resolve_thread_for_display())
    with TestClient(runner.create_app(), raise_server_exceptions=True) as client:
        yield client


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


def test_resolves_thread_owned_by_user(api_client):
    thread_id = str(ObjectId())
    display_id = str(ObjectId())
    ThreadEntity.create_thread(
        name="t",
        users=[User(user_id=TEST_USER_OID)],
        agents=[AgentInstanceRef(agent_id="a1", agent_class="TestAgent")],
        thread_id=ObjectId(thread_id),
    )
    _persist_display_event(thread_id, display_id)

    response = api_client.get(f"{EVENTS_BASE}/agents/displays/{display_id}/thread")

    assert response.status_code == 200, response.text
    assert response.json()["thread_id"] == thread_id


def test_returns_404_for_unknown_display(api_client):
    response = api_client.get(f"{EVENTS_BASE}/agents/displays/{str(ObjectId())}/thread")
    assert response.status_code == 404, response.text


# Note: the endpoint enforces thread access with the same guard as `get_agent_events_in_thread`
# (user-in-thread OR access-to-process). The fixed test identity has `aihub.admin.>`, so the 403
# branch is not reachable here — matching the sibling endpoint, which likewise has no 403 API test.


def test_aitl_delegation_resolves_single_thread(api_client):
    thread_id = str(ObjectId())
    display_id = str(ObjectId())
    ThreadEntity.create_thread(
        name="t",
        users=[User(user_id=TEST_USER_OID)],
        agents=[AgentInstanceRef(agent_id="namespace", agent_class="TestAgent")],
        thread_id=ObjectId(thread_id),
    )
    _persist_display_event(thread_id, display_id, agent_id="namespace", run_id="r1")
    _persist_display_event(thread_id, display_id, agent_id="rag", run_id="r2")

    response = api_client.get(f"{EVENTS_BASE}/agents/displays/{display_id}/thread")

    assert response.status_code == 200, response.text
    assert response.json()["thread_id"] == thread_id
