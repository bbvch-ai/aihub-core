import time
from collections.abc import AsyncIterator, Iterator
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dagster import (
    DagsterInstance,
    DagsterRunStatus,
    DefaultSensorStatus,
    JobDefinition,
    RunRequest,
    SensorDefinition,
    build_sensor_context,
    job,
    op,
)
from swiss_ai_hub.core.events.pipeline import SourceUpdatedEvent
from swiss_ai_hub.core.polling import PolledMessage

from swiss_ai_hub.pipeline.sensors.nats.nats_document_uploaded_sensor import nats_document_uploaded_sensor
from swiss_ai_hub.pipeline.sensors.nats.observation_run_decider import DEBOUNCE_SECONDS
from swiss_ai_hub.pipeline.sensors.nats.observation_sensor_cursor import ObservationSensorCursor
from swiss_ai_hub.pipeline.util.partition_utils import PARTITIONS_TRUNCATED_TAG

_MODULE = "swiss_ai_hub.pipeline.sensors.nats.nats_document_uploaded_sensor"


@op
def _noop() -> None: ...


@job
def observation_job() -> None:
    _noop()


def _topic_manager() -> MagicMock:
    topic_manager = MagicMock()
    topic_manager.source_type = "datalake"
    topic_manager.source_id = "bucket"
    topic_manager.target_type = "knowledge"
    topic_manager.target_id = "db"
    topic_manager.get_stream.return_value = ("stream", "subject.>")
    return topic_manager


def _message(sequence: int) -> MagicMock:
    message = MagicMock(spec=PolledMessage)
    message.event = SourceUpdatedEvent(path=f"docs/{sequence}.pdf")
    message.sequence = sequence
    message.ack = AsyncMock()
    message.nak = AsyncMock()
    return message


@contextmanager
def _nats_yielding(messages: list[MagicMock]) -> Iterator[None]:
    """Stub out the NATS connection and poller so only the sensor's decisions are exercised."""
    remaining = [messages] if messages else []

    async def _poll(*_args, **_kwargs) -> AsyncIterator[MagicMock]:
        current = remaining.pop(0) if remaining else []
        for message in current:
            yield message

    poller = MagicMock()
    poller.poll = _poll
    poller.ensure_stream_exists = AsyncMock()
    poller.ensure_consumer_exists = AsyncMock()

    connection = MagicMock()
    connection.jetstream = MagicMock(return_value=MagicMock())
    connection.close = AsyncMock()

    with (
        patch(f"{_MODULE}.NatsSettings.create_client", new=AsyncMock(return_value=connection)),
        patch(f"{_MODULE}.JSPoller", return_value=poller),
    ):
        yield


def _evaluate(
    sensor: SensorDefinition,
    instance: DagsterInstance,
    cursor: ObservationSensorCursor | None = None,
    messages: list[MagicMock] | None = None,
):
    context = build_sensor_context(instance=instance, cursor=cursor.model_dump_json() if cursor else None)
    with _nats_yielding(messages or []):
        return sensor.evaluate_tick(context)


def _start_run(instance: DagsterInstance, target: JobDefinition = observation_job) -> str:
    """Seeds a STARTED run: QUEUED needs a remote job origin, and the guard treats both alike."""
    return instance.create_run_for_job(target, status=DagsterRunStatus.STARTED).run_id


def _launch_requested_run(instance: DagsterInstance, result) -> None:
    """Stands in for the daemon, which turns a RunRequest into a run tagged with its run key.

    Without this a later tick correctly notices the request never launched and asks again.
    """
    for run_request in result.run_requests:
        run = instance.create_run_for_job(
            observation_job,
            status=DagsterRunStatus.STARTED,
            tags={"dagster/run_key": run_request.run_key},
        )
        instance.report_run_canceled(run)


@pytest.fixture
def sensor() -> SensorDefinition:
    return nats_document_uploaded_sensor(observation_job, _topic_manager())


@pytest.fixture
def instance() -> Iterator[DagsterInstance]:
    with DagsterInstance.ephemeral() as ephemeral:
        yield ephemeral


class TestSensorMetadata:
    def test_returns_sensor_with_expected_metadata(self, sensor: SensorDefinition) -> None:
        assert isinstance(sensor, SensorDefinition)
        assert sensor.name == "NATSDocumentUploadedSensorFor_observation_job"
        assert sensor.default_status is DefaultSensorStatus.RUNNING
        assert sensor.minimum_interval_seconds == 60


class TestSingleFlight:
    def test_events_arriving_during_a_run_skip_and_arm_a_followup(
        self, sensor: SensorDefinition, instance: DagsterInstance
    ) -> None:
        run_id = _start_run(instance)

        result = _evaluate(sensor, instance, messages=[_message(1)])

        assert not result.run_requests
        assert run_id in result.skip_message
        assert ObservationSensorCursor.from_cursor(result.cursor).followup_armed is True

    def test_the_followup_is_requested_once_the_run_is_terminal(
        self, sensor: SensorDefinition, instance: DagsterInstance
    ) -> None:
        """The snapshot-race guard: a file uploaded after a running observation listed the bucket
        must not be dropped."""
        run_id = _start_run(instance)
        during = _evaluate(sensor, instance, messages=[_message(1)])
        instance.report_run_canceled(instance.get_run_by_id(run_id))

        after = _evaluate(sensor, instance, cursor=ObservationSensorCursor.from_cursor(during.cursor))

        assert len(after.run_requests) == 1

    def test_a_run_launched_by_hand_also_suppresses_the_sensor(
        self, sensor: SensorDefinition, instance: DagsterInstance
    ) -> None:
        """The guard filters by job name, not by sensor, so manual runs count too."""
        _start_run(instance)

        result = _evaluate(sensor, instance, messages=[_message(1)])

        assert not result.run_requests

    def test_a_run_of_another_job_does_not_suppress_the_sensor(
        self, sensor: SensorDefinition, instance: DagsterInstance
    ) -> None:
        @job
        def unrelated_job() -> None:
            _noop()

        _start_run(instance, unrelated_job)
        cursor = ObservationSensorCursor(pending_events=1, first_pending_at=0.0)

        result = _evaluate(sensor, instance, cursor=cursor)

        assert len(result.run_requests) == 1


class TestDebounce:
    def test_a_fresh_burst_is_held(self, sensor: SensorDefinition, instance: DagsterInstance) -> None:
        result = _evaluate(sensor, instance, messages=[_message(1)])

        assert not result.run_requests
        assert ObservationSensorCursor.from_cursor(result.cursor).pending_events == 1

    def test_a_whole_backlog_drains_into_one_request(self, sensor: SensorDefinition, instance: DagsterInstance) -> None:
        """250 events in one tick must produce exactly one run, not one run per ten events."""
        aged = ObservationSensorCursor(pending_events=1, first_pending_at=0.0)

        result = _evaluate(sensor, instance, cursor=aged, messages=[_message(n) for n in range(1, 251)])

        assert len(result.run_requests) == 1
        assert ObservationSensorCursor.from_cursor(result.cursor).pending_events == 0

    def test_events_are_acked_only_after_the_outcome_is_settled(
        self, sensor: SensorDefinition, instance: DagsterInstance
    ) -> None:
        messages = [_message(1)]
        aged = ObservationSensorCursor(pending_events=1, first_pending_at=0.0)

        _evaluate(sensor, instance, cursor=aged, messages=messages)

        messages[0].ack.assert_awaited_once()


class TestRunKeys:
    def test_run_key_is_derived_from_the_stream_sequence(
        self, sensor: SensorDefinition, instance: DagsterInstance
    ) -> None:
        aged = ObservationSensorCursor(pending_events=1, first_pending_at=0.0)

        result = _evaluate(sensor, instance, cursor=aged, messages=[_message(17)])

        assert result.run_requests[0].run_key == "bucket_to_db_seq_17_r0"

    def test_the_same_backlog_yields_a_key_dagster_would_deduplicate(
        self, sensor: SensorDefinition, instance: DagsterInstance
    ) -> None:
        """Two ticks that saw the same events must not produce two distinct keys, so Dagster's own
        idempotence check becomes a second line of defence rather than being defeated."""
        aged = ObservationSensorCursor(pending_events=1, first_pending_at=0.0)

        first = _evaluate(sensor, instance, cursor=aged, messages=[_message(5)])
        second = _evaluate(sensor, instance, cursor=aged, messages=[_message(5)])

        assert first.run_requests[0].run_key == second.run_requests[0].run_key

    def test_a_batch_of_already_seen_sequences_gets_a_distinct_key(
        self, sensor: SensorDefinition, instance: DagsterInstance
    ) -> None:
        """A recreated or restored stream restarts its sequence numbering, so a real batch can carry
        sequences the cursor has already folded in. The key must still change, or Dagster's
        idempotence check drops the run being re-armed and the trigger is lost silently."""
        cursor = ObservationSensorCursor(
            max_sequence=100,
            requested_run_key="bucket_to_db_seq_100_r0",
            followup_armed=True,
        )
        launched = instance.create_run_for_job(
            observation_job,
            status=DagsterRunStatus.STARTED,
            tags={"dagster/run_key": "bucket_to_db_seq_100_r0"},
        )
        instance.report_run_canceled(launched)

        result = _evaluate(sensor, instance, cursor=cursor, messages=[_message(50)])

        assert result.run_requests[0].run_key != cursor.requested_run_key

    def test_a_rearm_without_new_events_gets_a_distinct_key(
        self, sensor: SensorDefinition, instance: DagsterInstance
    ) -> None:
        """A follow-up carrying no new events leaves the sequence unchanged, so the key must be
        distinguished from the one already requested or Dagster discards the run being re-armed."""
        cursor = ObservationSensorCursor(
            max_sequence=5,
            requested_run_key="bucket_to_db_seq_5_r0",
            followup_armed=True,
        )
        launched = instance.create_run_for_job(
            observation_job,
            status=DagsterRunStatus.STARTED,
            tags={"dagster/run_key": "bucket_to_db_seq_5_r0"},
        )
        instance.report_run_canceled(launched)

        result = _evaluate(sensor, instance, cursor=cursor)

        assert result.run_requests[0].run_key == "bucket_to_db_seq_5_r1"

    def test_a_first_request_does_not_burn_a_rearm_counter(
        self, sensor: SensorDefinition, instance: DagsterInstance
    ) -> None:
        """Nothing was requested before, so there is no key to collide with."""
        aged = ObservationSensorCursor(pending_events=1, first_pending_at=0.0)

        result = _evaluate(sensor, instance, cursor=aged, messages=[_message(5)])

        assert result.run_requests[0].run_key == "bucket_to_db_seq_5_r0"


class TestRecovery:
    def test_a_requested_run_that_never_launched_is_requested_again(
        self, sensor: SensorDefinition, instance: DagsterInstance
    ) -> None:
        """The daemon creates the run after the sensor returns, so a crash in that window would
        otherwise strand the batch until the nightly schedule."""
        cursor = ObservationSensorCursor(requested_run_key="bucket_to_db_seq_9_r0", max_sequence=9)

        result = _evaluate(sensor, instance, cursor=cursor)

        assert len(result.run_requests) == 1

    def test_an_unparseable_cursor_does_not_wedge_the_sensor(
        self, sensor: SensorDefinition, instance: DagsterInstance
    ) -> None:
        context = build_sensor_context(instance=instance, cursor="{not valid json")
        with _nats_yielding([]):
            result = sensor.evaluate_tick(context)

        assert not result.run_requests


class TestTruncationReArm:
    def test_a_truncating_run_re_arms_the_sensor(self, sensor: SensorDefinition, instance: DagsterInstance) -> None:
        """A run that hit max_partitions only observed part of the corpus, so single-flight must
        not leave the remainder waiting for the nightly schedule."""
        run_id = _start_run(instance)
        instance.add_run_tags(run_id, PARTITIONS_TRUNCATED_TAG)
        instance.report_run_canceled(instance.get_run_by_id(run_id))

        result = _evaluate(sensor, instance)

        assert len(result.run_requests) == 1
        assert ObservationSensorCursor.from_cursor(result.cursor).handled_truncation == run_id

    def test_the_same_truncating_run_does_not_re_arm_twice(
        self, sensor: SensorDefinition, instance: DagsterInstance
    ) -> None:
        run_id = _start_run(instance)
        instance.add_run_tags(run_id, PARTITIONS_TRUNCATED_TAG)
        instance.report_run_canceled(instance.get_run_by_id(run_id))
        first = _evaluate(sensor, instance)
        _launch_requested_run(instance, first)

        second = _evaluate(sensor, instance, cursor=ObservationSensorCursor.from_cursor(first.cursor))

        assert not second.run_requests


class TestFailureHandling:
    def test_a_failing_tick_naks_the_batch_for_redelivery(
        self, sensor: SensorDefinition, instance: DagsterInstance
    ) -> None:
        """Acking before the run is requested is what lets a failed tick drop its trigger."""
        messages = [_message(1)]
        context = build_sensor_context(instance=instance, cursor=None)

        with (
            _nats_yielding(messages),
            patch.object(type(instance), "get_run_records", side_effect=RuntimeError("event log unavailable")),
            pytest.raises(RuntimeError),
        ):
            list(sensor(context))

        messages[0].nak.assert_awaited_once()
        messages[0].ack.assert_not_awaited()


class TestDebounceBoundary:
    def test_a_burst_still_inside_the_debounce_is_held(
        self, sensor: SensorDefinition, instance: DagsterInstance
    ) -> None:
        fresh = ObservationSensorCursor(pending_events=2, first_pending_at=time.time())

        assert not _evaluate(sensor, instance, cursor=fresh).run_requests

    def test_a_burst_older_than_the_debounce_fires(self, sensor: SensorDefinition, instance: DagsterInstance) -> None:
        aged = ObservationSensorCursor(pending_events=2, first_pending_at=time.time() - DEBOUNCE_SECONDS)

        result = _evaluate(sensor, instance, cursor=aged)

        assert isinstance(result.run_requests[0], RunRequest)
