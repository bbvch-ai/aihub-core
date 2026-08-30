from collections.abc import Iterator

import pytest
from dagster import DagsterInstance, DagsterRunStatus, job, op

from swiss_ai_hub.pipeline.sensors.nats.observation_run_history import ObservationRunHistory
from swiss_ai_hub.pipeline.util.partition_utils import PARTITIONS_TRUNCATED_TAG


@op
def _noop() -> None: ...


@job
def observation_job() -> None:
    _noop()


@pytest.fixture
def instance() -> Iterator[DagsterInstance]:
    with DagsterInstance.ephemeral() as ephemeral:
        yield ephemeral


def _finished_run(instance: DagsterInstance, tags: dict[str, str] | None = None) -> str:
    run = instance.create_run_for_job(observation_job, status=DagsterRunStatus.STARTED, tags=tags)
    instance.report_run_canceled(run)
    return run.run_id


class TestLatestTruncatingRunId:
    def test_no_truncating_run_returns_none(self, instance: DagsterInstance) -> None:
        _finished_run(instance)

        assert ObservationRunHistory.latest_truncating_run_id(instance, observation_job.name) is None

    def test_returns_the_truncating_run(self, instance: DagsterInstance) -> None:
        run_id = _finished_run(instance, tags=PARTITIONS_TRUNCATED_TAG)

        assert ObservationRunHistory.latest_truncating_run_id(instance, observation_job.name) == run_id

    def test_returns_the_newest_of_several(self, instance: DagsterInstance) -> None:
        """Regression guard for a silent failure mode: the sensor re-arms only when this run id
        differs from the one its cursor already answered. If the oldest were returned instead, a
        second truncation would never be answered and those documents would go unobserved.
        """
        run_ids = [_finished_run(instance, tags=PARTITIONS_TRUNCATED_TAG) for _ in range(3)]

        assert ObservationRunHistory.latest_truncating_run_id(instance, observation_job.name) == run_ids[-1]

    def test_ignores_other_jobs(self, instance: DagsterInstance) -> None:
        @job
        def unrelated_job() -> None:
            _noop()

        run = instance.create_run_for_job(unrelated_job, status=DagsterRunStatus.STARTED, tags=PARTITIONS_TRUNCATED_TAG)
        instance.report_run_canceled(run)

        assert ObservationRunHistory.latest_truncating_run_id(instance, observation_job.name) is None


class TestRunExistsForRunKey:
    def test_missing_run_key_is_reported_absent(self, instance: DagsterInstance) -> None:
        assert ObservationRunHistory.run_exists_for_run_key(instance, observation_job.name, "never_launched") is False

    def test_launched_run_key_is_found(self, instance: DagsterInstance) -> None:
        _finished_run(instance, tags={"dagster/run_key": "bucket_to_db_seq_7_r0"})

        assert ObservationRunHistory.run_exists_for_run_key(instance, observation_job.name, "bucket_to_db_seq_7_r0")
