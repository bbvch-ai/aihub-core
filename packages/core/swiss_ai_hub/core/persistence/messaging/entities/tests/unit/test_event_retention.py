"""Age-bounded pruning of events in scheduled threads.

`event_data.created_at` is nanoseconds from `time.time_ns()`, not a BSON date, so a Mongo TTL index
cannot do this job and the cutoff has to be compared numerically. These tests pin the two properties
that follow from that: the right rows go, and a row whose timestamp cannot be compared stays.
"""

import time
from datetime import UTC, datetime, timedelta

import pytest
from mongoengine import connect, disconnect

from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.persistence.messaging.entities.persisted_agent_event_entity import PersistedAgentEventEntity

_NOW = datetime.now(UTC)
_SCHEDULED_THREAD = "6a87d2a27b1beebdd20a1443"
_OTHER_THREAD = "6a87d2a27b1beebdd20a1444"


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


def _event(thread_id: str, event_id: str, age: timedelta | None = None, created_at: object = None) -> None:
    if created_at is None:
        created_at = time.time_ns() if age is None else int((_NOW - age).timestamp() * 1_000_000_000)
    PersistedAgentEventEntity(
        agent_class="CronDemoAgent",
        agent_id="demo",
        thread_id=thread_id,
        display_id="d1",
        run_id="r1",
        event_id=event_id,
        event_type="control_event",
        event_name="CronStartEvent",
        event_data={"created_at": created_at},
        event_parents=["StartEvent"],
    ).save()


def _remaining() -> set[str]:
    return {event.event_id for event in PersistedAgentEventEntity.objects()}


class TestDeleteEventsOlderThan:
    def test_deletes_only_events_past_the_cutoff(self) -> None:
        _event(_SCHEDULED_THREAD, "old", age=timedelta(days=30))
        _event(_SCHEDULED_THREAD, "recent", age=timedelta(hours=1))

        deleted = PersistedAgentEventEntity.delete_events_older_than([_SCHEDULED_THREAD], _NOW - timedelta(days=7))

        assert deleted == 1
        assert _remaining() == {"recent"}

    def test_leaves_other_threads_alone(self) -> None:
        """Only threads derived from a live scheduled profile are ever passed in, and this is what makes
        over-deletion impossible even if that list were wrong."""
        _event(_SCHEDULED_THREAD, "scheduled-old", age=timedelta(days=30))
        _event(_OTHER_THREAD, "chat-old", age=timedelta(days=30))

        PersistedAgentEventEntity.delete_events_older_than([_SCHEDULED_THREAD], _NOW - timedelta(days=7))

        assert _remaining() == {"chat-old"}

    def test_keeps_an_event_whose_timestamp_cannot_be_compared(self) -> None:
        """A missing or non-numeric timestamp cannot match a `<` on an integer, so it is kept. Failing
        closed is the right way round for a delete."""
        _event(_SCHEDULED_THREAD, "unstamped", created_at="not-a-number")
        _event(_SCHEDULED_THREAD, "old", age=timedelta(days=30))

        PersistedAgentEventEntity.delete_events_older_than([_SCHEDULED_THREAD], _NOW - timedelta(days=7))

        assert _remaining() == {"unstamped"}

    def test_deletes_across_more_threads_than_one_batch(self) -> None:
        """Threads are chunked so an oversized `$in` cannot exceed FerretDB's limits."""
        threads = [f"6a87d2a27b1beebdd20a1{index:03d}" for index in range(120)]
        for thread in threads:
            _event(thread, f"old-{thread}", age=timedelta(days=30))

        deleted = PersistedAgentEventEntity.delete_events_older_than(threads, _NOW - timedelta(days=7), batch_size=50)

        assert deleted == 120
        assert _remaining() == set()

    def test_rejects_a_naive_cutoff(self) -> None:
        """ThreadEntity.created_at is written naive, so a naive cutoff here would quietly mean local time
        and delete a different amount of history depending on where the process runs."""
        with pytest.raises(ValueError, match="timezone-aware"):
            PersistedAgentEventEntity.delete_events_older_than([_SCHEDULED_THREAD], datetime.now())

    def test_no_threads_deletes_nothing(self) -> None:
        _event(_SCHEDULED_THREAD, "old", age=timedelta(days=30))

        assert PersistedAgentEventEntity.delete_events_older_than([], _NOW - timedelta(days=7)) == 0
        assert _remaining() == {"old"}
