from dagster import DefaultScheduleStatus, ScheduleDefinition
from dagster._core.definitions.target import ExecutableDefinition


def create_schedule_definition(
    job: ExecutableDefinition,
    cron_schedule: str,
    description: str,
    default_status: DefaultScheduleStatus = DefaultScheduleStatus.RUNNING,
    execution_timezone: str = "Europe/Berlin",
    name: str = None,
) -> ScheduleDefinition:
    return ScheduleDefinition(
        name=name,
        job=job,
        description=description,
        cron_schedule=cron_schedule,
        default_status=default_status,
        execution_timezone=execution_timezone,
    )


def daily_schedule_at(job: ExecutableDefinition, hour: int, minute: int = 0) -> ScheduleDefinition:
    return create_schedule_definition(
        job=job,
        cron_schedule=f"{minute} {hour} * * *",
        name=f"PeriodicObservationAt_{hour:02}_{minute:02}_{job.name}",
        description=f"Schedules the job to run daily at {hour:02}:{minute:02}.",
    )


def default_daily_materialize_schedule(job: ExecutableDefinition) -> ScheduleDefinition:
    """Schedules the job execution to run daily at 2am."""
    return daily_schedule_at(job=job, hour=2, minute=0)
