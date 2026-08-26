from datetime import UTC, datetime, timedelta

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


def _persist_cost_event(
    event_id: str,
    user_id: str | None = None,
    tenant_id: str | None = None,
    prompt: float = 0.0,
    completion: float = 0.0,
    embedding: float | None = None,
    created_at: int | None = None,
) -> None:
    """Insert one LLMCostEvent. `embedding=None` omits the field entirely, as chat-only events do.

    Defaults to now rather than a fixed timestamp: the aggregation applies a default time window, so a
    hard-coded date would silently age out of it and turn every unfiltered assertion into an empty result.
    """
    created_at = created_at if created_at is not None else int(datetime.now(UTC).timestamp() * 1e9)
    event_data = {
        "created_at": created_at,
        "user_id": user_id,
        "tenant_id": tenant_id,
        "prompt_tokens_costs": prompt,
        "completion_tokens_costs": completion,
    }
    if embedding is not None:
        event_data["embedding_tokens_costs"] = embedding

    PersistedAgentEventEntity(
        agent_class="TestAgent",
        agent_id="test",
        thread_id="t_spend",
        display_id="disp",
        run_id="run",
        event_id=event_id,
        event_type=AgentTopicManager.DISPLAY_EVENT,
        event_name="LLMCostEvent",
        event_data=event_data,
        event_parents=["LLMCostEvent", "CostEvent", "DisplayEvent"],
    ).save()


class TestLLMSpendAggregation:
    def test_groups_and_sums_per_user(self):
        _persist_cost_event("e1", user_id="u1", tenant_id="acme", prompt=1.0, completion=2.0)
        _persist_cost_event("e2", user_id="u1", tenant_id="acme", prompt=0.5, completion=0.25)
        _persist_cost_event("e3", user_id="u2", tenant_id="acme", prompt=4.0)

        spend = {row.user_id: row for row in PersistedAgentEventEntity.get_llm_spend_by_user()}

        assert spend["u1"].calls == 2
        assert spend["u1"].total_costs == pytest.approx(3.75)
        assert spend["u1"].prompt_tokens_costs == pytest.approx(1.5)
        assert spend["u2"].calls == 1
        assert spend["u2"].total_costs == pytest.approx(4.0)

    def test_groups_per_tenant_across_users(self):
        _persist_cost_event("e1", user_id="u1", tenant_id="acme", prompt=1.0)
        _persist_cost_event("e2", user_id="u2", tenant_id="acme", prompt=2.0)
        _persist_cost_event("e3", user_id="u3", tenant_id="globex", prompt=5.0)

        spend = {row.tenant_id: row for row in PersistedAgentEventEntity.get_llm_spend_by_tenant()}

        assert spend["acme"].calls == 2
        assert spend["acme"].total_costs == pytest.approx(3.0)
        assert spend["globex"].total_costs == pytest.approx(5.0)

    def test_duplicate_event_id_counted_once(self):
        """~16% of real cost events are persisted twice; counting both would inflate every bill."""
        _persist_cost_event("dup", user_id="u1", tenant_id="acme", prompt=2.0)
        _persist_cost_event("dup", user_id="u1", tenant_id="acme", prompt=2.0)

        spend = PersistedAgentEventEntity.get_llm_spend_by_user()

        assert len(spend) == 1
        assert spend[0].calls == 1
        assert spend[0].total_costs == pytest.approx(2.0)

    def test_absent_embedding_cost_does_not_poison_the_sum(self):
        """`$add` over a missing field yields null, which would zero out the whole row without `$ifNull`."""
        _persist_cost_event("e1", user_id="u1", tenant_id="acme", prompt=1.0, completion=2.0, embedding=None)

        spend = PersistedAgentEventEntity.get_llm_spend_by_user()

        assert spend[0].total_costs == pytest.approx(3.0)
        assert spend[0].embedding_tokens_costs == 0.0

    def test_tenant_filter_excludes_other_tenants(self):
        """The endpoint relies on this to keep one tenant's admin from seeing another tenant's users."""
        _persist_cost_event("e1", user_id="u1", tenant_id="acme", prompt=1.0)
        _persist_cost_event("e2", user_id="u2", tenant_id="globex", prompt=9.0)

        spend = PersistedAgentEventEntity.get_llm_spend_by_user(tenant_id="acme")

        assert [row.user_id for row in spend] == ["u1"]
        assert spend[0].total_costs == pytest.approx(1.0)
        # The rows are tenant-scoped, so they must say so — a null tenant would read as "no tenant".
        assert spend[0].tenant_id == "acme"

    def test_since_excludes_older_events(self):

        cutoff = datetime(2025, 1, 1, tzinfo=UTC)
        older = int(datetime(2024, 6, 1, tzinfo=UTC).timestamp() * 1e9)
        newer = int(datetime(2025, 6, 1, tzinfo=UTC).timestamp() * 1e9)
        _persist_cost_event("old", user_id="u1", tenant_id="acme", prompt=8.0, created_at=older)
        _persist_cost_event("new", user_id="u1", tenant_id="acme", prompt=1.0, created_at=newer)

        spend = PersistedAgentEventEntity.get_llm_spend_by_user(since=cutoff)

        assert spend[0].calls == 1
        assert spend[0].total_costs == pytest.approx(1.0)

    def test_naive_since_is_read_as_utc(self):
        """FastAPI hands us a naive datetime for `?since=...`; reading it as server-local time would
        shift the cutoff by the host's UTC offset and silently include or exclude hours of spend."""

        just_after = int(datetime(2025, 1, 1, 1, 0, tzinfo=UTC).timestamp() * 1e9)
        _persist_cost_event("e1", user_id="u1", tenant_id="acme", prompt=1.0, created_at=just_after)

        naive_cutoff = datetime(2025, 1, 1, 0, 0)
        aware_cutoff = datetime(2025, 1, 1, 0, 0, tzinfo=UTC)

        assert PersistedAgentEventEntity.get_llm_spend_by_user(since=naive_cutoff) == (
            PersistedAgentEventEntity.get_llm_spend_by_user(since=aware_cutoff)
        )

    def test_unfiltered_rows_carry_the_tenant(self):
        """The cross-tenant view is the one place per-tenant spend is readable — LiteLLM cannot carry
        tenant at all — so a row without it leaves an operator unable to tell whose spend it is."""
        _persist_cost_event("e1", user_id="u1", tenant_id="acme", prompt=1.0)
        _persist_cost_event("e2", user_id="u2", tenant_id="globex", prompt=2.0)

        spend = {row.user_id: row for row in PersistedAgentEventEntity.get_llm_spend_by_user()}

        assert spend["u1"].tenant_id == "acme"
        assert spend["u2"].tenant_id == "globex"

    def test_a_user_acting_in_two_tenants_is_split_per_tenant(self):
        """Spend belongs to the tenant it was incurred in; collapsing both into one row would bill a
        tenant for usage that happened elsewhere."""
        _persist_cost_event("e1", user_id="u1", tenant_id="acme", prompt=1.0)
        _persist_cost_event("e2", user_id="u1", tenant_id="globex", prompt=2.0)

        rows = sorted(PersistedAgentEventEntity.get_llm_spend_by_user(), key=lambda row: row.tenant_id)

        assert [(row.user_id, row.tenant_id) for row in rows] == [("u1", "acme"), ("u1", "globex")]
        assert rows[0].total_costs == pytest.approx(1.0)
        assert rows[1].total_costs == pytest.approx(2.0)

    def test_default_window_bounds_an_unfiltered_request(self):
        """Without a cutoff the match narrows to `event_parents` alone and the dedup stage builds one
        group per cost event ever persisted, which trips Mongo's 100MB `$group` limit in production."""
        window = PersistedAgentEventEntity.SPEND_WINDOW_DAYS
        outside = int((datetime.now(UTC) - timedelta(days=window + 1)).timestamp() * 1e9)
        inside = int((datetime.now(UTC) - timedelta(days=1)).timestamp() * 1e9)
        _persist_cost_event("old", user_id="u1", tenant_id="acme", prompt=8.0, created_at=outside)
        _persist_cost_event("new", user_id="u1", tenant_id="acme", prompt=1.0, created_at=inside)

        spend = PersistedAgentEventEntity.get_llm_spend_by_user()

        assert spend[0].calls == 1
        assert spend[0].total_costs == pytest.approx(1.0)

    def test_explicit_since_overrides_the_default_window(self):
        """An operator asking for a year of history must get it, not the default window."""
        window = PersistedAgentEventEntity.SPEND_WINDOW_DAYS
        outside = int((datetime.now(UTC) - timedelta(days=window + 1)).timestamp() * 1e9)
        _persist_cost_event("old", user_id="u1", tenant_id="acme", prompt=8.0, created_at=outside)

        spend = PersistedAgentEventEntity.get_llm_spend_by_user(since=datetime.now(UTC) - timedelta(days=window + 30))

        assert spend[0].total_costs == pytest.approx(8.0)

    def test_non_cost_events_are_ignored(self):
        _persist_event("t_spend", ["StartEvent"], "s1")
        _persist_cost_event("e1", user_id="u1", tenant_id="acme", prompt=1.0)

        spend = PersistedAgentEventEntity.get_llm_spend_by_user()

        assert len(spend) == 1
        assert spend[0].calls == 1
