from dagster import RunRequest, ScheduleDefinition, ScheduleEvaluationContext, schedule
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.unresolved_asset_job_definition import UnresolvedAssetJobDefinition


def daily_backup_schedule(backup_job: JobDefinition | UnresolvedAssetJobDefinition) -> ScheduleDefinition:
    @schedule(cron_schedule="0 2 * * *", job=backup_job, execution_timezone="Europe/Zurich")
    def daily_backup_schedule(context: ScheduleEvaluationContext) -> RunRequest:
        return RunRequest()

    return daily_backup_schedule
