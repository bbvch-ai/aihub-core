from collections.abc import Iterator
from datetime import timedelta

import pytest
from dagster import (
    AssetExecutionContext,
    DagsterEvent,
    DagsterEventType,
    DagsterInstance,
    DagsterRunStatus,
    DefaultSensorStatus,
    Definitions,
    DynamicPartitionsDefinition,
    JobDefinition,
    RunRequest,
    SkipReason,
    asset,
    build_run_status_sensor_context,
    define_asset_job,
    job,
    op,
)

import swiss_ai_hub.pipeline.sensors.unlanded_partition_retry_sensor as sensor_module
from swiss_ai_hub.pipeline.sensors.unlanded_partition_retry_sensor import unlanded_partition_retry_sensor
from swiss_ai_hub.pipeline.util.run_routing import BUCKET_RUN_TAG
from swiss_ai_hub.pipeline.util.unlanded_partition_retry_config import UnlandedPartitionRetryConfig

_PARTITIONS = DynamicPartitionsDefinition(name="sensor_test_source_partitions")
_FAIL_TAG = "test/fail"


@asset(partitions_def=_PARTITIONS)
def data_lake_files(context: AssetExecutionContext) -> None:
    if context.run.tags.get(_FAIL_TAG):
        raise RuntimeError("S3 gateway unavailable")


@op
def _noop() -> None: ...


@job
def observe_job() -> None:
    _noop()


_DEFS = Definitions(
    assets=[data_lake_files],
    jobs=[
        define_asset_job("automation", selection=[data_lake_files], partitions_def=_PARTITIONS),
        define_asset_job("retry_unlanded_files", selection=[data_lake_files], partitions_def=_PARTITIONS),
    ],
)
_AUTOMATION: JobDefinition = _DEFS.resolve_job_def("automation")
_RETRY: JobDefinition = _DEFS.resolve_job_def("retry_unlanded_files")
_CONFIG = UnlandedPartitionRetryConfig(
    asset_key=data_lake_files.key, retry_job_name=_RETRY.name, max_attempts=3, base_delay=timedelta(0)
)


@pytest.fixture
def instance() -> Iterator[DagsterInstance]:
    with DagsterInstance.ephemeral() as ephemeral:
        yield ephemeral


def _sensor():
    return unlanded_partition_retry_sensor(
        monitored_job=observe_job, retry_job=_RETRY, config=_CONFIG, partitions=_PARTITIONS
    )


def _failed_write(instance: DagsterInstance, key: str, job_def: JobDefinition = _AUTOMATION) -> None:
    instance.add_dynamic_partitions(_PARTITIONS.name, [key])
    job_def.execute_in_process(instance=instance, partition_key=key, tags={_FAIL_TAG: "1"}, raise_on_error=False)


def _evaluate(instance: DagsterInstance, tags: dict[str, str]) -> list[RunRequest | SkipReason]:
    observation = instance.create_run_for_job(observe_job, status=DagsterRunStatus.SUCCESS, tags=tags)
    context = build_run_status_sensor_context(
        sensor_name=_sensor().name,
        dagster_event=DagsterEvent(event_type_value=DagsterEventType.RUN_SUCCESS.value, job_name=observe_job.name),
        dagster_instance=instance,
        dagster_run=observation,
    )
    return list(_sensor()(context))


class TestDefinition:
    def test_follows_the_observation_and_runs_by_default(self) -> None:
        sensor = _sensor()

        assert sensor.name == "retry_unlanded_partitions_after_observe_job"
        assert sensor.default_status is DefaultSensorStatus.RUNNING
        assert sensor.job_name == _RETRY.name

    def test_a_retry_job_other_than_the_counted_one_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="attempts are counted"):
            unlanded_partition_retry_sensor(
                monitored_job=observe_job, retry_job=_AUTOMATION, config=_CONFIG, partitions=_PARTITIONS
            )


class TestRequests:
    def test_a_failed_file_is_requested_with_the_bucket_tag(self, instance: DagsterInstance) -> None:
        _failed_write(instance, "hrdocs|a%2Fone.pdf")

        [request] = _evaluate(instance, {BUCKET_RUN_TAG: "hrdocs"})

        assert isinstance(request, RunRequest)
        assert request.partition_key == "hrdocs|a%2Fone.pdf"
        assert request.tags[BUCKET_RUN_TAG] == "hrdocs"

    def test_only_the_observed_bucket_is_retried(self, instance: DagsterInstance) -> None:
        _failed_write(instance, "hrdocs|a%2Fone.pdf")
        _failed_write(instance, "finance|a%2Fone.pdf")

        requests = _evaluate(instance, {BUCKET_RUN_TAG: "hrdocs"})

        assert [request.partition_key for request in requests] == ["hrdocs|a%2Fone.pdf"]

    def test_an_observation_without_a_bucket_tag_is_skipped(self, instance: DagsterInstance) -> None:
        _failed_write(instance, "hrdocs|a%2Fone.pdf")

        [result] = _evaluate(instance, {})

        assert isinstance(result, SkipReason)

    def test_nothing_due_is_a_skip(self, instance: DagsterInstance) -> None:
        [result] = _evaluate(instance, {BUCKET_RUN_TAG: "hrdocs"})

        assert isinstance(result, SkipReason)


class TestRunKeys:
    def test_the_run_key_is_stable_while_the_attempt_is_pending(self, instance: DagsterInstance) -> None:
        _failed_write(instance, "hrdocs|a%2Fone.pdf")

        [first] = _evaluate(instance, {BUCKET_RUN_TAG: "hrdocs"})
        [second] = _evaluate(instance, {BUCKET_RUN_TAG: "hrdocs"})

        assert first.run_key == second.run_key

    def test_the_run_key_moves_on_once_the_attempt_finished(self, instance: DagsterInstance) -> None:
        _failed_write(instance, "hrdocs|a%2Fone.pdf")
        [before] = _evaluate(instance, {BUCKET_RUN_TAG: "hrdocs"})
        _failed_write(instance, "hrdocs|a%2Fone.pdf", _RETRY)

        [after] = _evaluate(instance, {BUCKET_RUN_TAG: "hrdocs"})

        assert after.run_key != before.run_key


class TestPerTickCap:
    def test_requests_are_capped_per_tick(self, instance: DagsterInstance, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sensor_module, "MAX_RETRY_REQUESTS_PER_TICK", 2)
        for name in ("one", "two", "three"):
            _failed_write(instance, f"hrdocs|a%2F{name}.pdf")

        requests = _evaluate(instance, {BUCKET_RUN_TAG: "hrdocs"})

        assert len(requests) == 2
        assert all(isinstance(request, RunRequest) for request in requests)
