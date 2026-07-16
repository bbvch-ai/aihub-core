from dagster import DefaultScheduleStatus, RunRequest, ScheduleEvaluationContext, schedule
from dagster._core.definitions.target import ExecutableDefinition
from swiss_ai_hub.core.persistence import BucketEntity

from swiss_ai_hub.pipeline.util.bucket_utils import ensure_main_db_connection
from swiss_ai_hub.pipeline.util.run_routing import BUCKET_RUN_TAG


def per_bucket_observe_schedule(
    observe_job: ExecutableDefinition,
    *,
    ingestor: str,
    hour: int,
    minute: int = 0,
    execution_timezone: str = "Europe/Berlin",
) -> schedule:
    """Daily schedule that fans out one observe run per knowledge database it owns.

    Enumerates ``BucketEntity`` owned by this pipeline (``ingestor``) at evaluation time and yields one
    bucket-tagged ``RunRequest`` each, so databases created after deployment are observed automatically on
    the next tick — no code-location reload.
    """

    @schedule(
        job=observe_job,
        cron_schedule=f"{minute} {hour} * * *",
        name=f"PerBucketObservationAt_{hour:02}_{minute:02}",
        description="Observes the data lake of every knowledge database this pipeline owns once per day.",
        default_status=DefaultScheduleStatus.RUNNING,
        execution_timezone=execution_timezone,
    )
    def _schedule(context: ScheduleEvaluationContext):
        ensure_main_db_connection()
        timestamp = int(context.scheduled_execution_time.timestamp())
        for bucket in BucketEntity.get_all_buckets():
            if bucket.ingestor != ingestor:
                continue
            yield RunRequest(
                run_key=f"{bucket.bucket_name}_{timestamp}",
                tags={BUCKET_RUN_TAG: bucket.bucket_name},
            )

    return _schedule
