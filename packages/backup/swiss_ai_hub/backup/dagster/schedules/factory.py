from __future__ import annotations

from typing import TYPE_CHECKING

from dagster import JobDefinition, RunRequest, ScheduleEvaluationContext, schedule

if TYPE_CHECKING:
    from dagster import ScheduleDefinition
    from dagster._core.definitions.unresolved_asset_job_definition import UnresolvedAssetJobDefinition


def daily_backup_schedule(backup_job: JobDefinition | UnresolvedAssetJobDefinition) -> ScheduleDefinition:
    """Must finish before the pipeline observation schedule (default 2 AM) in aihub_pipeline.

    The backup stops all application containers — if it overlaps with a pipeline
    job, that job is killed mid-execution.
    """

    @schedule(cron_schedule="0 1 * * *", job=backup_job, execution_timezone="Europe/Zurich")
    def daily_backup(context: ScheduleEvaluationContext) -> RunRequest:
        return RunRequest()

    return daily_backup
