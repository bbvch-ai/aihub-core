import pytest
from mongoengine import connect, disconnect

from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.persistence.messaging.entities.persisted_agent_event_entity import PersistedAgentEventEntity
from swiss_ai_hub.core.topic_managers.agents.agent_topic_manager import AgentTopicManager


@pytest.fixture
def mongo_connection():
    connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
    )
    yield
    disconnect()


@pytest.fixture(autouse=True)
def clean_events(mongo_connection):
    PersistedAgentEventEntity.objects.delete()
    yield
    PersistedAgentEventEntity.objects.delete()


def _persist_event(
    thread_id: str,
    event_parents: list[str],
    event_id: str,
    event_type: str = AgentTopicManager.CONTROL_EVENT,
    display_id: str = "disp",
    agent_id: str = "test",
    run_id: str = "run",
) -> None:
    """Insert a minimal event. Only thread_id / event_id / event_parents / event_type drive classification."""
    PersistedAgentEventEntity(
        agent_class="TestAgent",
        agent_id=agent_id,
        thread_id=thread_id,
        display_id=display_id,
        run_id=run_id,
        event_id=event_id,
        event_type=event_type,
        event_name=event_parents[0],
        event_data={"created_at": 1_730_000_000_000_000_000},
        event_parents=event_parents,
    ).save()


class TestThreadIdsByStatus:
    def test_exception_event_makes_thread_failed(self):
        _persist_event("t_fail", ["ExceptionEvent"], "e1")
        assert PersistedAgentEventEntity.thread_ids_by_status("failed") == ["t_fail"]
        assert PersistedAgentEventEntity.thread_ids_by_status("active") == []
        assert PersistedAgentEventEntity.thread_ids_by_status("completed") == []

    def test_unbalanced_start_is_active(self):
        _persist_event("t_active", ["StartEvent"], "e1")
        assert PersistedAgentEventEntity.thread_ids_by_status("active") == ["t_active"]
        assert PersistedAgentEventEntity.thread_ids_by_status("completed") == []

    def test_balanced_start_stop_is_completed(self):
        _persist_event("t_done", ["StartEvent"], "e1")
        _persist_event("t_done", ["StopEvent"], "e2")
        assert PersistedAgentEventEntity.thread_ids_by_status("completed") == ["t_done"]
        assert PersistedAgentEventEntity.thread_ids_by_status("active") == []

    def test_failed_takes_precedence_over_active(self):
        _persist_event("t1", ["StartEvent"], "e1")
        _persist_event("t1", ["ExceptionEvent"], "e2")
        assert PersistedAgentEventEntity.thread_ids_by_status("failed") == ["t1"]
        assert PersistedAgentEventEntity.thread_ids_by_status("active") == []

    def test_duplicate_event_id_is_not_double_counted(self):
        _persist_event("t_dup", ["StartEvent"], "e1")
        _persist_event("t_dup", ["StopEvent"], "e2")
        _persist_event("t_dup", ["StartEvent"], "e1")
        assert PersistedAgentEventEntity.thread_ids_by_status("completed") == ["t_dup"]
        assert PersistedAgentEventEntity.thread_ids_by_status("active") == []

    def test_start_event_must_be_control_type(self):
        _persist_event("t_disp", ["StartEvent"], "e1", event_type=AgentTopicManager.DISPLAY_EVENT)
        assert PersistedAgentEventEntity.thread_ids_by_status("active") == []
        assert PersistedAgentEventEntity.thread_ids_by_status("completed") == ["t_disp"]

    def test_thread_with_no_events_is_in_no_bucket(self):
        assert PersistedAgentEventEntity.thread_ids_by_status("active") == []
        assert PersistedAgentEventEntity.thread_ids_by_status("completed") == []
        assert PersistedAgentEventEntity.thread_ids_by_status("failed") == []

    def test_thread_ids_param_scopes_the_aggregation(self):
        _persist_event("t_a", ["StartEvent"], "e1")
        _persist_event("t_b", ["StartEvent"], "e2")
        assert PersistedAgentEventEntity.thread_ids_by_status("active", thread_ids=["t_a"]) == ["t_a"]

    def test_multiple_threads_same_status_returned_unordered(self):
        _persist_event("t_x", ["ExceptionEvent"], "e1")
        _persist_event("t_y", ["ExceptionEvent"], "e2")
        # the pipeline has no $sort, so compare as a set
        assert set(PersistedAgentEventEntity.thread_ids_by_status("failed")) == {"t_x", "t_y"}


class TestThreadIdForDisplay:
    def test_resolves_thread_from_display(self):
        _persist_event("t_owner", ["StartEvent"], "e1", display_id="d1")
        assert PersistedAgentEventEntity.thread_id_for_display("d1") == "t_owner"

    def test_returns_none_for_unknown_display(self):
        assert PersistedAgentEventEntity.thread_id_for_display("missing") is None

    def test_aitl_delegation_shares_one_thread_for_a_display(self):
        # NamespaceSelectionAgent -> RAGAgent: same thread_id + display_id, different agent/run.
        _persist_event("t_shared", ["StartEvent"], "e1", display_id="d1", agent_id="namespace", run_id="r1")
        _persist_event("t_shared", ["StartEvent"], "e2", display_id="d1", agent_id="rag", run_id="r2")
        assert PersistedAgentEventEntity.thread_id_for_display("d1") == "t_shared"

    def test_distinct_displays_resolve_to_their_own_threads(self):
        # Side-by-side: each column is a separate message -> distinct display_id -> distinct thread.
        _persist_event("t_a", ["StartEvent"], "e1", display_id="d_a")
        _persist_event("t_b", ["StartEvent"], "e2", display_id="d_b")
        assert PersistedAgentEventEntity.thread_id_for_display("d_a") == "t_a"
        assert PersistedAgentEventEntity.thread_id_for_display("d_b") == "t_b"
