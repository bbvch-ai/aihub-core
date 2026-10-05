from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from dagster import (
    AssetExecutionContext,
    DagsterInstance,
    DagsterRunStatus,
    Definitions,
    DynamicPartitionsDefinition,
    JobDefinition,
    asset,
    define_asset_job,
)
from dagster._core.storage.tags import PARTITION_NAME_TAG

from swiss_ai_hub.pipeline.util.unlanded_partition_retry_config import UnlandedPartitionRetryConfig
from swiss_ai_hub.pipeline.util.unlanded_partitions import UnlandedPartitions

_PARTITIONS = DynamicPartitionsDefinition(name="test_source_partitions")
_FAIL_TAG = "test/fail"
_KEY = "hrdocs|Policies%2Fhandbook.pdf"


@asset(partitions_def=_PARTITIONS)
def data_lake_files(context: AssetExecutionContext) -> None:
    if context.run.tags.get(_FAIL_TAG):
        raise RuntimeError("S3 gateway unavailable")


_DEFS = Definitions(
    assets=[data_lake_files],
    jobs=[
        define_asset_job("automation", selection=[data_lake_files], partitions_def=_PARTITIONS),
        define_asset_job("retry", selection=[data_lake_files], partitions_def=_PARTITIONS),
    ],
)
_AUTOMATION: JobDefinition = _DEFS.resolve_job_def("automation")
_RETRY: JobDefinition = _DEFS.resolve_job_def("retry")


def _config(max_attempts: int = 3, base_delay: timedelta = timedelta(0)) -> UnlandedPartitionRetryConfig:
    return UnlandedPartitionRetryConfig(
        asset_key=data_lake_files.key, retry_job_name=_RETRY.name, max_attempts=max_attempts, base_delay=base_delay
    )


@pytest.fixture
def instance() -> Iterator[DagsterInstance]:
    with DagsterInstance.ephemeral() as ephemeral:
        ephemeral.add_dynamic_partitions(_PARTITIONS.name, [_KEY])
        yield ephemeral


def _run(instance: DagsterInstance, job: JobDefinition, *, fail: bool) -> None:
    job.execute_in_process(
        instance=instance, partition_key=_KEY, tags={_FAIL_TAG: "1"} if fail else {}, raise_on_error=False
    )


def _unfinished(instance: DagsterInstance, job: JobDefinition, status: DagsterRunStatus) -> None:
    instance.create_run_for_job(
        job, status=status, tags={PARTITION_NAME_TAG: _KEY}, asset_selection={data_lake_files.key}
    )


def _find(instance: DagsterInstance, config: UnlandedPartitionRetryConfig | None = None, now: datetime | None = None):
    return UnlandedPartitions.find(instance, config or _config(), _PARTITIONS, [_KEY], now or datetime.now(UTC))


class TestCandidates:
    def test_a_failed_partition_is_retried(self, instance: DagsterInstance) -> None:
        _run(instance, _AUTOMATION, fail=True)

        report = _find(instance)

        assert [retry.partition_key for retry in report.to_retry] == [_KEY]
        assert report.to_retry[0].attempt == 1
        assert report.missing_from_data_lake == 1

    def test_a_missing_partition_that_already_had_a_run_is_retried(self, instance: DagsterInstance) -> None:
        """A canceled run leaves the partition neither failed nor in progress, but it did not land."""
        run = instance.create_run_for_job(
            _AUTOMATION, tags={PARTITION_NAME_TAG: _KEY}, asset_selection={data_lake_files.key}
        )
        instance.report_run_canceled(run)

        assert [retry.partition_key for retry in _find(instance).to_retry] == [_KEY]

    def test_a_never_attempted_partition_is_left_to_eager(self, instance: DagsterInstance) -> None:
        report = _find(instance)

        assert report.to_retry == []
        assert report.missing_from_data_lake == 0

    def test_a_landed_partition_is_not_a_candidate(self, instance: DagsterInstance) -> None:
        _run(instance, _AUTOMATION, fail=False)

        assert _find(instance).missing_from_data_lake == 0

    def test_an_in_progress_partition_is_skipped(self, instance: DagsterInstance) -> None:
        _run(instance, _AUTOMATION, fail=True)
        _unfinished(instance, _RETRY, DagsterRunStatus.STARTED)

        report = _find(instance)

        assert report.in_progress == [_KEY]
        assert report.to_retry == []


class TestAttemptCeiling:
    def test_the_ceiling_moves_the_partition_to_exhausted(self, instance: DagsterInstance) -> None:
        _run(instance, _AUTOMATION, fail=True)
        for _ in range(3):
            _run(instance, _RETRY, fail=True)

        report = _find(instance)

        assert report.exhausted == [_KEY]
        assert report.to_retry == []
        assert report.missing_from_data_lake == 1

    def test_attempts_below_the_ceiling_are_numbered(self, instance: DagsterInstance) -> None:
        _run(instance, _AUTOMATION, fail=True)
        _run(instance, _RETRY, fail=True)

        retry = _find(instance).to_retry[0]

        assert retry.attempt == 2
        assert retry.run_number == 1

    def test_a_success_resets_the_counter_but_not_the_run_key(self, instance: DagsterInstance) -> None:
        """Dagster deduplicates run keys forever, so the key keeps counting while the attempt restarts."""
        _run(instance, _AUTOMATION, fail=True)
        for _ in range(3):
            _run(instance, _RETRY, fail=True)
        _run(instance, _AUTOMATION, fail=False)
        _run(instance, _AUTOMATION, fail=True)

        retry = _find(instance).to_retry[0]

        assert retry.attempt == 1
        assert retry.run_number == 3
        assert retry.run_key.endswith("_3")


class TestBackoff:
    def test_a_recent_attempt_waits_out_the_base_delay(self, instance: DagsterInstance) -> None:
        _run(instance, _AUTOMATION, fail=True)
        _run(instance, _RETRY, fail=True)

        report = _find(instance, _config(base_delay=timedelta(minutes=10)))

        assert report.backing_off == [_KEY]
        assert report.to_retry == []
        assert report.missing_from_data_lake == 1

    def test_the_delay_doubles_with_each_attempt(self, instance: DagsterInstance) -> None:
        _run(instance, _AUTOMATION, fail=True)
        _run(instance, _RETRY, fail=True)
        _run(instance, _RETRY, fail=True)
        config = _config(base_delay=timedelta(minutes=10))

        after_fifteen = _find(instance, config, datetime.now(UTC) + timedelta(minutes=15))
        after_twenty_five = _find(instance, config, datetime.now(UTC) + timedelta(minutes=25))

        assert after_fifteen.backing_off == [_KEY]
        assert [retry.partition_key for retry in after_twenty_five.to_retry] == [_KEY]

    def test_the_first_retry_does_not_wait(self, instance: DagsterInstance) -> None:
        _run(instance, _AUTOMATION, fail=True)

        report = _find(instance, _config(base_delay=timedelta(minutes=10)))

        assert [retry.partition_key for retry in report.to_retry] == [_KEY]


class TestRunKey:
    def test_the_run_key_hashes_the_composite_key(self, instance: DagsterInstance) -> None:
        _run(instance, _AUTOMATION, fail=True)

        run_key = _find(instance).to_retry[0].run_key

        assert run_key.startswith("retry_")
        assert "|" not in run_key
        assert "%" not in run_key
