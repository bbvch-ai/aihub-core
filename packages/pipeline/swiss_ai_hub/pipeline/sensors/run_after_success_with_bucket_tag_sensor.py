import logging

from dagster import (
    DagsterRunStatus,
    DefaultSensorStatus,
    JobDefinition,
    RunRequest,
    RunStatusSensorContext,
    SensorDefinition,
    run_status_sensor,
)

from swiss_ai_hub.pipeline.util.run_routing import BUCKET_RUN_TAG

logger = logging.getLogger(__name__)


def run_after_success_with_bucket_tag_sensor(
    *,
    monitored_job: JobDefinition,
    triggered_job: JobDefinition,
    name: str | None = None,
) -> SensorDefinition:
    """Triggers ``triggered_job`` after a successful ``monitored_job`` run, propagating the bucket tag.

    The RAG pipeline routes every run by its ``aihub/bucket`` tag, so the cleanup (remove) run must
    inherit the same bucket as the observe run it follows — otherwise its tag-routed stores would resolve to
    the wrong (or no) knowledge database.
    """
    sensor_name = name or f"trigger_{triggered_job.name}_after_{monitored_job.name}"

    @run_status_sensor(
        name=sensor_name,
        run_status=DagsterRunStatus.SUCCESS,
        monitored_jobs=[monitored_job],
        request_job=triggered_job,
        default_status=DefaultSensorStatus.RUNNING,
    )
    def _sensor(context: RunStatusSensorContext) -> RunRequest | None:
        bucket = context.dagster_run.tags.get(BUCKET_RUN_TAG)
        if not bucket:
            logger.warning(
                f"Observe run {context.dagster_run.run_id} has no '{BUCKET_RUN_TAG}' tag; skipping cleanup trigger."
            )
            return None
        return RunRequest(run_key=context.dagster_run.run_id, tags={BUCKET_RUN_TAG: bucket})

    return _sensor
