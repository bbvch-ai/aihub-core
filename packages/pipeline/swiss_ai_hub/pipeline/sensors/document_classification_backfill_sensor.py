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
from swiss_ai_hub.core.persistence import BucketEntity

from swiss_ai_hub.pipeline.ops.repair.backfill_document_classification_op import (
    BackfillDocumentClassificationConfig,
)
from swiss_ai_hub.pipeline.util.bucket_utils import ensure_main_db_connection
from swiss_ai_hub.pipeline.util.run_routing import BUCKET_RUN_TAG

logger = logging.getLogger(__name__)

BACKFILL_TARGET_TAG = "aihub/classification_backfill"
BACKFILL_REQUEST_TAG = "aihub/classification_requested_at"
MAX_ATTEMPTS_PER_REQUEST = 3


def document_classification_backfill_sensor(
    job: ExecutableDefinition,
    *,
    ingestor: Annotated[str, "Ingestor whose databases this pipeline serves"],
):
    """Runs the classification backfill for every database of this ingestor whose classification was requested.

    The request is a time on the database's row, set by the API, and it is the work queue, as `deleting` is for the
    teardown sensor: whatever is still requested is still owed. The run clears the request it was started for, so a
    request made while it ran survives and starts the next one. A request whose runs failed `MAX_ATTEMPTS_PER_REQUEST`
    times is given up and kept as failed, so an outage cannot start a run every tick until someone notices.
    """

    @sensor(
        job=job,
        minimum_interval_seconds=60,
        default_status=DefaultSensorStatus.RUNNING,
        name=f"DocumentClassificationBackfillSensorFor_{job.name}",
        description="Requests a classification backfill for each knowledge database that asked for one.",
    )
    def _sensor(context: SensorEvaluationContext):
        ensure_main_db_connection()
        requested = [
            bucket for bucket in BucketEntity.get_classification_requested_buckets() if bucket.ingestor == ingestor
        ]
        run_requests = [
            request
            for bucket in requested
            if (request := _run_request_for(context.instance, job.name, bucket.bucket_name, bucket))
        ]
        if run_requests:
            yield from run_requests
            return
        yield SkipReason(f"{len(requested)} backfill(s) requested, none ready to (re)start.")

    return _sensor


def _run_request_for(
    instance: DagsterInstance, job_name: str, bucket_name: str, bucket: BucketEntity
) -> RunRequest | None:
    """A request for this database's backfill, unless one is running, this attempt was already requested, or the
    request used up its attempts.

    Keyed by the request time and the number of runs that request has had, as the teardown sensor keys its runs: the
    key stays the same while an attempt is pending, and moves on once it finished, so a failed run is driven again.
    A run that succeeds clears its request, so every earlier run of a request still owed is one that failed.
    """
    target_tag = {BACKFILL_TARGET_TAG: bucket_name}
    if instance.get_run_records(
        RunsFilter(job_name=job_name, tags=target_tag, statuses=list(NOT_FINISHED_STATUSES)), limit=1
    ):
        return None

    requested_at = bucket.classification_requested_at.isoformat()
    request_tags = target_tag | {BACKFILL_REQUEST_TAG: requested_at}
    attempt = instance.get_runs_count(RunsFilter(job_name=job_name, tags=request_tags))
    if attempt >= MAX_ATTEMPTS_PER_REQUEST:
        logger.warning(f"Giving up the classification backfill of '{bucket_name}' after {attempt} failed runs")
        BucketEntity.fail_classification_request(bucket_name, bucket.classification_requested_at)
        return None
    logger.info(f"Requesting a classification backfill of '{bucket_name}' (attempt {attempt})")
    return RunRequest(
        run_key=f"classification_backfill_{bucket_name}_{requested_at}_{attempt}",
        run_config=RunConfig(
            ops={
                "backfill_document_classification_op": BackfillDocumentClassificationConfig(
                    dry_run=False, requested_at=requested_at
                )
            }
        ),
        tags=request_tags | {BUCKET_RUN_TAG: bucket_name},
    )
