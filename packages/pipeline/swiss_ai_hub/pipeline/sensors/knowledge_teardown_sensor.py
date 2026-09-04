import logging
from typing import Annotated

from dagster import (
    DagsterInstance,
    DefaultSensorStatus,
    RunConfig,
    RunRequest,
    RunsFilter,
    SensorEvaluationContext,
    SkipReason,
    sensor,
)
from dagster._core.definitions.target import ExecutableDefinition
from dagster._core.storage.dagster_run import NOT_FINISHED_STATUSES
from swiss_ai_hub.core.persistence import BucketEntity, NamespaceEntity

from swiss_ai_hub.pipeline.ops.teardown.knowledge_teardown_op import KnowledgeTeardownConfig
from swiss_ai_hub.pipeline.util.bucket_utils import ensure_main_db_connection
from swiss_ai_hub.pipeline.util.run_routing import BUCKET_RUN_TAG

logger = logging.getLogger(__name__)

TEARDOWN_TARGET_TAG = "aihub/teardown_target"


def knowledge_teardown_sensor(
    job: ExecutableDefinition,
    *,
    ingestor: Annotated[str, "Ingestor whose databases this pipeline serves"],
):
    """Runs the teardown job for every knowledge database or namespace flagged ``deleting``.

    The flag itself is the work queue, not a message: the API sets it in the same write that hides the row
    from the UI, and it survives until the teardown job removes the row. An event-driven teardown could be
    acknowledged and then lost — by a daemon crash, or by a publish that never happened — and nothing would
    ever re-drive it, stranding the database invisible and un-purged. Reading the flag makes the sensor
    convergent instead: whatever is still flagged is still owed.
    """
    partition_registry_name = f"{ingestor}_document_partitions"

    @sensor(
        job=job,
        minimum_interval_seconds=30,
        default_status=DefaultSensorStatus.RUNNING,
        name=f"KnowledgeTeardownSensorFor_{job.name}",
        description="Requests a teardown run for each knowledge database or namespace flagged for deletion.",
    )
    def _sensor(context: SensorEvaluationContext):
        ensure_main_db_connection()

        buckets_by_id = {
            str(bucket.id): bucket for bucket in BucketEntity.get_all_buckets() if bucket.ingestor == ingestor
        }
        deleting_bucket_ids = {
            str(bucket.id) for bucket in BucketEntity.get_deleting_buckets() if str(bucket.id) in buckets_by_id
        }

        configs: list[tuple[str, str, KnowledgeTeardownConfig]] = []

        for bucket_id in sorted(deleting_bucket_ids):
            bucket = buckets_by_id[bucket_id]
            configs.append(
                (
                    bucket_id,
                    bucket.bucket_name,
                    KnowledgeTeardownConfig(
                        teardown_type="database",
                        bucket_id=bucket_id,
                        bucket_name=bucket.bucket_name,
                        db_name=bucket.db_name,
                        partition_registry_name=partition_registry_name,
                    ),
                )
            )

        for namespace in NamespaceEntity.get_deleting_namespaces():
            bucket = buckets_by_id.get(namespace.bucket_id)
            if bucket is None:
                continue
            # A database teardown flags the bucket and all of its namespaces; the database job already
            # drops every namespace's data wholesale, so a per-namespace run would be redundant work.
            if namespace.bucket_id in deleting_bucket_ids:
                continue
            configs.append(
                (
                    str(namespace.id),
                    bucket.bucket_name,
                    KnowledgeTeardownConfig(
                        teardown_type="namespace",
                        bucket_id=namespace.bucket_id,
                        bucket_name=bucket.bucket_name,
                        db_name=bucket.db_name,
                        partition_registry_name=partition_registry_name,
                        namespace_id=str(namespace.id),
                        namespace_name=namespace.namespace_name,
                        folder_name=namespace.folder_name,
                    ),
                )
            )

        run_requests = [
            request
            for target_id, bucket_name, config in configs
            if (request := _run_request_for(context.instance, job.name, target_id, bucket_name, config))
        ]

        if run_requests:
            yield from run_requests
            return
        yield SkipReason(f"{len(configs)} teardown(s) flagged, none ready to (re)start.")

    return _sensor


def _run_request_for(
    instance: DagsterInstance,
    job_name: str,
    target_id: Annotated[str, "Entity id of the bucket or namespace being torn down"],
    bucket_name: str,
    config: KnowledgeTeardownConfig,
) -> RunRequest | None:
    """A request for this target, unless one is already running or this attempt was already requested.

    Dagster deduplicates run keys forever, so a key derived from the entity id alone would make a failed
    teardown unretryable. Numbering the key by how many runs the target has already had keeps it stable
    while an attempt is pending — repeated ticks re-request the same key, which Dagster drops — and moves
    it on only once that attempt has finished, which is exactly when a re-drive is wanted.
    """
    target_tag = {TEARDOWN_TARGET_TAG: target_id}

    if instance.get_run_records(
        RunsFilter(job_name=job_name, tags=target_tag, statuses=list(NOT_FINISHED_STATUSES)), limit=1
    ):
        return None

    attempt = instance.get_runs_count(RunsFilter(job_name=job_name, tags=target_tag))
    logger.info(f"Requesting teardown of {config.teardown_type} '{target_id}' (attempt {attempt})")

    return RunRequest(
        run_key=f"teardown_{target_id}_{attempt}",
        run_config=RunConfig(ops={"knowledge_teardown_op": config}),
        tags=target_tag | {BUCKET_RUN_TAG: bucket_name},
    )
