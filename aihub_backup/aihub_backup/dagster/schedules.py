import dagster as dg

from aihub_backup.dagster.config import BackupConfig
from aihub_backup.dagster.jobs import backup_asset_job


@dg.schedule(
    cron_schedule="0 2 * * *",
    job=backup_asset_job,
    execution_timezone="Europe/Zurich",
)
def daily_backup_schedule(context: dg.ScheduleEvaluationContext) -> dg.RunRequest:
    """Trigger a daily online backup at 2 AM Zurich time, targeting today's partition."""
    # Dagster guarantees scheduled_execution_time is set for schedule callbacks
    scheduled_time = context.scheduled_execution_time
    if scheduled_time is None:
        raise RuntimeError("scheduled_execution_time unexpectedly None in schedule callback")

    today = scheduled_time.strftime("%Y-%m-%d")
    return dg.RunRequest(
        partition_key=today,
        run_config=dg.RunConfig(ops={"create_backup": BackupConfig(mode="online")}),
    )
