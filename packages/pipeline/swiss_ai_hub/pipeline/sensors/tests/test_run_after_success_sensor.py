from collections.abc import Iterator

import pytest
from dagster import (
    DagsterEvent,
    DagsterEventType,
    DagsterInstance,
    DagsterRunStatus,
    DefaultSensorStatus,
    RunRequest,
    SkipReason,
    build_run_status_sensor_context,
    job,
    op,
)

from swiss_ai_hub.pipeline.sensors.run_after_success_sensor import run_after_success_sensor


@op
def _noop() -> None: ...


@job
def observe_job() -> None:
    _noop()


@job
def remove_job() -> None:
    _noop()


@pytest.fixture
def instance() -> Iterator[DagsterInstance]:
    with DagsterInstance.ephemeral() as ephemeral:
        yield ephemeral


def _evaluate(instance: DagsterInstance, observing_run_id: str) -> RunRequest | SkipReason:
    """Invokes the sensor body with a context standing in for a succeeded observation run."""
    sensor = run_after_success_sensor(monitored_job=observe_job, triggered_job=remove_job)
    dagster_run = instance.get_run_by_id(observing_run_id)
    context = build_run_status_sensor_context(
        sensor_name=sensor.name,
        dagster_event=DagsterEvent(
            event_type_value=DagsterEventType.RUN_SUCCESS.value,
            job_name=observe_job.name,
        ),
        dagster_instance=instance,
        dagster_run=dagster_run,
    )
    return sensor(context)


def _started_removal(instance: DagsterInstance) -> str:
    """A removal that is genuinely running: the RUN_START event is what populates ``start_time``."""
    run = instance.create_run_for_job(remove_job, status=DagsterRunStatus.STARTED)
    instance.report_dagster_event(
        DagsterEvent(event_type_value=DagsterEventType.RUN_START.value, job_name=remove_job.name),
        run_id=run.run_id,
    )
    return run.run_id


def _succeeded_observation(instance: DagsterInstance) -> str:
    run = instance.create_run_for_job(observe_job, status=DagsterRunStatus.STARTED)
    instance.report_run_canceled(run)
    return run.run_id


class TestSensorMetadata:
    def test_name_is_derived_from_both_jobs(self) -> None:
        sensor = run_after_success_sensor(monitored_job=observe_job, triggered_job=remove_job)

        assert sensor.name == "trigger_remove_job_after_observe_job"
        assert sensor.default_status is DefaultSensorStatus.RUNNING

    def test_explicit_name_wins(self) -> None:
        sensor = run_after_success_sensor(monitored_job=observe_job, triggered_job=remove_job, name="custom")

        assert sensor.name == "custom"


class TestSingleFlight:
    def test_requests_a_run_when_nothing_is_in_flight(self, instance: DagsterInstance) -> None:
        observing_run_id = _succeeded_observation(instance)

        result = _evaluate(instance, observing_run_id)

        assert isinstance(result, RunRequest)

    def test_run_key_is_the_observing_run_so_retries_deduplicate(self, instance: DagsterInstance) -> None:
        observing_run_id = _succeeded_observation(instance)

        result = _evaluate(instance, observing_run_id)

        assert result.run_key == observing_run_id

    def test_skips_when_the_in_flight_removal_started_after_this_observation(self, instance: DagsterInstance) -> None:
        """A removal that began after the observation finished snapshots the converged corpus, so
        it genuinely covers this observation."""
        observing_run_id = _succeeded_observation(instance)
        in_flight_id = _started_removal(instance)

        result = _evaluate(instance, observing_run_id)

        assert isinstance(result, SkipReason)
        assert in_flight_id in result.skip_message

    def test_requests_when_the_in_flight_removal_predates_this_observation(self, instance: DagsterInstance) -> None:
        """Regression guard: the older removal may have listed the corpus before this observation
        converged. Skipping would consume the trigger for good, leaving deleted documents in the
        doc and vector stores until some later observation happens to succeed."""
        _started_removal(instance)
        observing_run_id = _succeeded_observation(instance)

        result = _evaluate(instance, observing_run_id)

        assert isinstance(result, RunRequest)
        assert result.run_key == observing_run_id

    def test_requests_when_the_in_flight_removal_has_no_start_time(self, instance: DagsterInstance) -> None:
        """Queued but not yet started: without a start time the sensor cannot prove coverage, so it
        requests rather than risk dropping the trigger."""
        instance.create_run_for_job(remove_job, status=DagsterRunStatus.STARTED)
        observing_run_id = _succeeded_observation(instance)

        assert isinstance(_evaluate(instance, observing_run_id), RunRequest)

    def test_an_in_flight_observation_does_not_block_the_removal(self, instance: DagsterInstance) -> None:
        """The guard is scoped to the triggered job, not to every job in the code location."""
        instance.create_run_for_job(observe_job, status=DagsterRunStatus.STARTED)
        observing_run_id = _succeeded_observation(instance)

        assert isinstance(_evaluate(instance, observing_run_id), RunRequest)
