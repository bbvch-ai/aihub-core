import logging
import time
from collections import defaultdict
from collections.abc import Sequence
from importlib.metadata import version
from typing import Annotated

from dagster import (
    AssetKey,
    DagsterInstance,
    DagsterRunStatus,
    DefaultSensorStatus,
    DynamicPartitionsDefinition,
    RunRequest,
    RunsFilter,
    SensorEvaluationContext,
    SkipReason,
    sensor,
)
from dagster._core.definitions.unresolved_asset_job_definition import UnresolvedAssetJobDefinition
from dagster._core.storage.partition_status_cache import AssetPartitionStatus
from dagster._core.storage.tags import PARTITION_NAME_TAG, PRIORITY_TAG
from swiss_ai_hub.core.infrastructure import MongoConnectionRegistry
from swiss_ai_hub.core.persistence import BucketEntity, RefDoc

from swiss_ai_hub.pipeline.sensors.ingestion_retry_decider import IngestionRetryDecider
from swiss_ai_hub.pipeline.types.ingestion_attempt import INGESTION_RETRY_TAG, PIPELINE_VERSION_TAG, IngestionAttempt
from swiss_ai_hub.pipeline.types.ingestion_retry_action import IngestionRetryAction
from swiss_ai_hub.pipeline.types.ingestion_retry_decision import IngestionRetryDecision
from swiss_ai_hub.pipeline.util.bucket_utils import (
    ensure_main_db_connection,
    get_db_name_from_bucket_name,
    get_or_create_namespace_for_directory,
)
from swiss_ai_hub.pipeline.util.id_utils import uri_to_id
from swiss_ai_hub.pipeline.util.partition_utils import split_composite_partition_key
from swiss_ai_hub.pipeline.util.run_routing import BUCKET_RUN_TAG, bucket_from_partition_key, owned_by_ingestor

logger = logging.getLogger(__name__)

INGESTION_RETRY_ORIGIN_TAG = "aihub/ingestion_retry_origin"
# Below the default of 0, so a backlog of retries after a release never delays a fresh upload.
RETRY_RUN_PRIORITY = "-1"
# A release can make every document a bug left failed due at once; the rest follow on the next ticks.
MAX_RETRIES_PER_TICK = 50
# Runs read per failed partition: enough to reach the run that started the failure through many releases.
HISTORY_LIMIT = 100
# A queued run counts: the document is waiting for an attempt, which the knowledge list shows as processing.
UNFINISHED_RUN_STATUSES = [
    DagsterRunStatus.QUEUED,
    DagsterRunStatus.NOT_STARTED,
    DagsterRunStatus.STARTING,
    DagsterRunStatus.STARTED,
]


def failed_ingestion_retry_sensor(
    job: UnresolvedAssetJobDefinition,
    *,
    ingestor: Annotated[str, "Ingestor whose databases this pipeline serves"],
    asset_keys: Annotated[Sequence[AssetKey], "The document's partitioned assets, upstream first"],
    partitions: DynamicPartitionsDefinition,
    max_retries: int,
    backoff_minutes: int,
    encode_partition_keys: bool = True,
    pipeline_version: Annotated[str | None, "Defaults to the installed swiss-ai-hub-pipeline version"] = None,
):
    """Retries a document whose latest ingestion attempt failed, and reports the failure on its record.

    Automation materializes a partition when its file's data version changes, and a failed run changes nothing, so
    without this a failed document would wait for its file to change. The partition statuses Dagster keeps are the
    work queue, as the `deleting` flag is for the teardown sensor: whatever is still failed is still owed. Retries are
    bounded per pipeline version (see `IngestionRetryDecider`), so a file that can never be ingested stops after
    `max_retries`, and the release that fixes a bug retries what it left failed. A run it did not request clears the
    failure from the record while it is queued or running, so a changed file shows as processing, not as failed.
    """
    current_version = pipeline_version or version("swiss-ai-hub-pipeline")
    backoff_seconds = backoff_minutes * 60
    owns = owned_by_ingestor(ingestor)

    @sensor(
        job=job,
        minimum_interval_seconds=60,
        default_status=DefaultSensorStatus.RUNNING,
        name=f"FailedIngestionRetrySensorFor_{job.name}",
        description="Retries documents whose ingestion failed, a bounded number of times per pipeline version.",
    )
    def _sensor(context: SensorEvaluationContext):
        ensure_main_db_connection()
        owned_buckets = {bucket.bucket_name for bucket in BucketEntity.get_all_buckets() if owns(bucket)}
        partition_keys = [
            key
            for key in context.instance.get_dynamic_partitions(partitions.name)
            if bucket_from_partition_key(key) in owned_buckets
        ]
        _clear_failures_of_fresh_runs(context.instance, set(partition_keys), encode_partition_keys)
        failed = _earliest_failed_asset_by_partition(context.instance, asset_keys, partitions, partition_keys)

        run_requests: list[RunRequest] = []
        for partition_key, asset_key in failed.items():
            history = [
                IngestionAttempt.from_run_record(record)
                for record in context.instance.get_run_records(
                    RunsFilter(tags={PARTITION_NAME_TAG: partition_key}), limit=HISTORY_LIMIT
                )
            ]
            decision = IngestionRetryDecider.decide(
                history, current_version, max_retries, backoff_seconds, now=time.time()
            )
            if decision is None:
                continue
            _report_on_record(partition_key, decision, encode_partition_keys)
            if decision.action is IngestionRetryAction.RETRY and len(run_requests) < MAX_RETRIES_PER_TICK:
                run_requests.append(_run_request(partition_key, asset_key, decision, current_version))

        if run_requests:
            yield from run_requests
            return
        yield SkipReason(f"{len(failed)} failed partition(s), none due for a retry.")

    return _sensor


def _earliest_failed_asset_by_partition(
    instance: DagsterInstance,
    asset_keys: Sequence[AssetKey],
    partitions: DynamicPartitionsDefinition,
    partition_keys: list[str],
) -> dict[str, AssetKey]:
    """For each partition whose chain broke, the first asset that failed, unless one before it is still running.

    Retrying the earliest failed asset alone lets automation carry the rest of the chain as it does for a new file;
    requesting the downstream assets too would race the automation runs the upstream one triggers.
    """
    status_by_asset = {
        asset_key: instance.get_status_by_partition(asset_key, partition_keys, partitions) or {}
        for asset_key in asset_keys
    }
    failed: dict[str, AssetKey] = {}
    for partition_key in partition_keys:
        for asset_key in asset_keys:
            status = status_by_asset[asset_key].get(partition_key)
            if status is AssetPartitionStatus.IN_PROGRESS:
                break
            if status is AssetPartitionStatus.FAILED:
                failed[partition_key] = asset_key
                break
    return failed


def _report_on_record(partition_key: str, decision: IngestionRetryDecision, encode_partition_keys: bool) -> None:
    """Shows the failure on the document's record, creating a placeholder when the failure came before its first one.

    A file from a source pipeline gets its record only from a successful parse, so a parse that never succeeds would
    otherwise leave nothing in the knowledge list to show as failed.
    """
    bucket, file_uri = split_composite_partition_key(partition_key, encode=encode_partition_keys)
    db_name = get_db_name_from_bucket_name(bucket)
    MongoConnectionRegistry.ensure_alias(db_name)
    doc_id = uri_to_id(file_uri)
    failed_at = int(decision.failed_at or time.time())
    failure = {
        "failed_attempts": decision.failed_attempts,
        "gave_up": decision.action is IngestionRetryAction.GIVE_UP,
        "failed_at": failed_at,
    }
    # Rounded down, so the strict check also leaves alone a record changed within the second the attempt started.
    attempt_started_at = int(decision.attempt_started_at or failed_at)

    if RefDoc.record_ingestion_failure(
        db_alias=db_name, doc_id=doc_id, attempt_started_at=attempt_started_at, **failure
    ):
        return
    if RefDoc.get_existing_ids(db_alias=db_name, doc_ids=[doc_id]):
        return
    directory_name = file_uri.split("/")[3]
    RefDoc.create_failed_placeholder(
        db_name,
        source=file_uri,
        namespace=get_or_create_namespace_for_directory(bucket, directory_name),
        **failure,
    )


def _clear_failures_of_fresh_runs(
    instance: DagsterInstance, partition_keys: set[str], encode_partition_keys: bool
) -> None:
    """Shows a document whose file is being ingested afresh as processing again, rather than as its last failure.

    A run the retry sensor did not request starts a new failure, if any, and the API resets the record of an upload
    itself; a file that changed at its source has nothing else to reset it until its parse succeeds.
    """
    fresh_partition_keys = {
        record.dagster_run.tags.get(PARTITION_NAME_TAG)
        for record in instance.get_run_records(RunsFilter(statuses=UNFINISHED_RUN_STATUSES))
        if INGESTION_RETRY_TAG not in record.dagster_run.tags
    } & partition_keys
    doc_ids_by_bucket: dict[str, list[str]] = defaultdict(list)
    for partition_key in fresh_partition_keys:
        bucket, file_uri = split_composite_partition_key(partition_key, encode=encode_partition_keys)
        doc_ids_by_bucket[bucket].append(uri_to_id(file_uri))
    for bucket, doc_ids in doc_ids_by_bucket.items():
        db_name = get_db_name_from_bucket_name(bucket)
        MongoConnectionRegistry.ensure_alias(db_name)
        RefDoc.clear_ingestion_failures(db_name, doc_ids)


def _run_request(
    partition_key: str, asset_key: AssetKey, decision: IngestionRetryDecision, pipeline_version: str
) -> RunRequest:
    """Keyed by the failure's origin run, the pipeline version and the retry number: the key stays the same while a
    retry is pending, which Dagster deduplicates, and moves on once it finished. The origin keeps a file that changed
    and failed again from reusing the keys of its earlier failure."""
    logger.info(
        f"Retrying {asset_key.to_user_string()} of '{partition_key}' "
        f"(retry {decision.retry_number}, {decision.failed_attempts} failed attempt(s))"
    )
    return RunRequest(
        run_key=(
            f"ingestion_retry_{asset_key.path[-1]}_{partition_key}_{decision.origin_run_id}_"
            f"{pipeline_version}_{decision.retry_number}"
        ),
        partition_key=partition_key,
        asset_selection=[asset_key],
        tags={
            INGESTION_RETRY_TAG: "true",
            INGESTION_RETRY_ORIGIN_TAG: decision.origin_run_id,
            PIPELINE_VERSION_TAG: pipeline_version,
            BUCKET_RUN_TAG: bucket_from_partition_key(partition_key),
            PRIORITY_TAG: RETRY_RUN_PRIORITY,
        },
    )
