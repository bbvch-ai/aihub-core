import logging
from collections.abc import Iterator
from datetime import UTC, datetime

from dagster import (
    DagsterRunStatus,
    DefaultSensorStatus,
    DynamicPartitionsDefinition,
    JobDefinition,
    RunRequest,
    RunStatusSensorContext,
    SensorDefinition,
    SkipReason,
    run_status_sensor,
)

from swiss_ai_hub.pipeline.util.partition_utils import bucket_of_composite_partition_key
from swiss_ai_hub.pipeline.util.run_routing import BUCKET_RUN_TAG
from swiss_ai_hub.pipeline.util.unlanded_partition_retry_config import UnlandedPartitionRetryConfig
from swiss_ai_hub.pipeline.util.unlanded_partitions import UnlandedPartitions

logger = logging.getLogger(__name__)

# A long outage leaves every file of a database unlanded; the rest wait for the next observation rather than
# flooding the queue in one tick.
MAX_RETRY_REQUESTS_PER_TICK = 200


def unlanded_partition_retry_sensor(
    *,
    monitored_job: JobDefinition,
    retry_job: JobDefinition,
    config: UnlandedPartitionRetryConfig,
    partitions: DynamicPartitionsDefinition,
    name: str | None = None,
) -> SensorDefinition:
    """Re-requests the observed database's partitions that were attempted but never landed, after each observation.

    An observation with unchanged data versions does not re-fire ``eager()``, so without this a file whose write
    failed stays missing until it changes at the source. Hooking the observation bounds the attempts to one per
    observation, and the retry job's run count against ``config.max_attempts`` stops a deterministic failure.
    """
    if retry_job.name != config.retry_job_name:
        msg = f"Retry job '{retry_job.name}' is not the job attempts are counted for ('{config.retry_job_name}')."
        raise ValueError(msg)

    @run_status_sensor(
        name=name or f"retry_unlanded_partitions_after_{monitored_job.name}",
        run_status=DagsterRunStatus.SUCCESS,
        monitored_jobs=[monitored_job],
        request_job=retry_job,
        default_status=DefaultSensorStatus.RUNNING,
    )
    def _sensor(context: RunStatusSensorContext) -> Iterator[RunRequest | SkipReason]:
        bucket = context.dagster_run.tags.get(BUCKET_RUN_TAG)
        if not bucket:
            yield SkipReason(f"Observe run {context.dagster_run.run_id} has no '{BUCKET_RUN_TAG}' tag.")
            return

        bucket_keys = [
            key
            for key in context.instance.get_dynamic_partitions(partitions.name)
            if bucket_of_composite_partition_key(key) == bucket
        ]
        report = UnlandedPartitions.find(context.instance, config, partitions, bucket_keys, datetime.now(UTC))
        requested = report.to_retry[:MAX_RETRY_REQUESTS_PER_TICK]
        logger.info(
            f"'{bucket}': {report.missing_from_data_lake} partition(s) not landed, requesting {len(requested)}, "
            f"{len(report.backing_off)} backing off, {len(report.exhausted)} exhausted, "
            f"{len(report.in_progress)} in progress"
        )
        if not requested:
            yield SkipReason(f"No partition of '{bucket}' is due for a retry.")
            return
        for retry in requested:
            yield RunRequest(partition_key=retry.partition_key, run_key=retry.run_key, tags={BUCKET_RUN_TAG: bucket})

    return _sensor

