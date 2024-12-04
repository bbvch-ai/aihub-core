from dagster import DefaultScheduleStatus, ScheduleDefinition
from dagster._core.definitions.target import ExecutableDefinition


def default_daily_materialize_schedule(job: ExecutableDefinition) -> ScheduleDefinition:
    """Schedules the job execution to run daily at 2am."""
    return ScheduleDefinition(
        job=job,
        cron_schedule="0 2 * * *",
        default_status=DefaultScheduleStatus.RUNNING,
    )
