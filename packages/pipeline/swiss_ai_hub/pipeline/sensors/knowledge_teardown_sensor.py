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
from mongoengine import DoesNotExist
from swiss_ai_hub.core.persistence.rag.datalake.entities import BucketEntity, NamespaceEntity

from swiss_ai_hub.pipeline.ops.teardown.knowledge_teardown_op import KnowledgeTeardownConfig
from swiss_ai_hub.pipeline.util.bucket_utils import ensure_main_db_connection

logger = logging.getLogger(__name__)

TEARDOWN_TARGET_TAG = "aihub/teardown_target"


def knowledge_teardown_sensor(
    job: ExecutableDefinition,
    *,
    datalake_container_name: Annotated[str, "The single bucket this deploy-bound pipeline serves"],
):
    """Runs the teardown job for every namespace of this pipeline's bucket flagged ``deleting``.

    The flag itself is the work queue, not a message: the API sets it in the same write that hides the row
    from the UI, and it survives until the teardown job removes the row. An event-driven teardown could be
    acknowledged and then lost — by a daemon crash, or by a publish that never happened — and nothing would
    ever re-drive it, stranding the namespace invisible and un-purged. Reading the flag makes the sensor
    convergent instead: whatever is still flagged is still owed.

    This pipeline is bound to one bucket at deploy time, so the queue is an exact lookup rather than the scan
    a pipeline serving many databases would need.
    """

    @sensor(
        job=job,
        minimum_interval_seconds=30,
        default_status=DefaultSensorStatus.RUNNING,
        name=f"KnowledgeTeardownSensorFor_{job.name}",
        description="Requests a teardown run for each namespace of this bucket flagged for deletion.",
    )
    def _sensor(context: SensorEvaluationContext):
        ensure_main_db_connection()

        try:
            bucket = BucketEntity.get_bucket_by_bucket_name(datalake_container_name)
        except DoesNotExist:
            yield SkipReason(f"Bucket '{datalake_container_name}' has no metadata row; nothing to tear down.")
            return

        configs = [
            (
                str(namespace.id),
                KnowledgeTeardownConfig(
                    namespace_id=str(namespace.id),
                    namespace_name=namespace.namespace_name,
                    folder_name=namespace.folder_name,
                    db_name=bucket.db_name,
                ),
            )
            for namespace in NamespaceEntity.get_namespaces_by_bucket(str(bucket.id))
            if namespace.deleting
        ]

        run_requests = [
            request
            for target_id, config in configs
            if (request := _run_request_for(context.instance, job.name, target_id, config))
        ]

        if run_requests:
            yield from run_requests
            return
        yield SkipReason(f"{len(configs)} teardown(s) flagged, none ready to (re)start.")

    return _sensor


def _run_request_for(
    instance: DagsterInstance,
    job_name: str,
    target_id: Annotated[str, "Entity id of the namespace being torn down"],
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
    logger.info(f"Requesting teardown of namespace '{config.namespace_name}' (attempt {attempt})")

    return RunRequest(
        run_key=f"teardown_{target_id}_{attempt}",
        run_config=RunConfig(ops={"knowledge_teardown_op": config}),
        tags=target_tag,
    )
