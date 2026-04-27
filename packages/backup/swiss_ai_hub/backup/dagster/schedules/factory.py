from __future__ import annotations

from typing import TYPE_CHECKING

from dagster import JobDefinition, RunRequest, ScheduleEvaluationContext, SkipReason, schedule

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


def weekly_cleanup_schedule(cleanup_job: JobDefinition | UnresolvedAssetJobDefinition) -> ScheduleDefinition:
    """Sunday 3 AM Europe/Zurich — after the daily backup window closes.

    Cleanup is online-safe (no container stops) but we still want it adjacent
    to the backup slot so all Postgres-heavy work happens in one nightly window
    rather than scattered across the day.
    """

    @schedule(cron_schedule="0 3 * * 0", job=cleanup_job, execution_timezone="Europe/Zurich")
    def weekly_cleanup(context: ScheduleEvaluationContext) -> RunRequest:
        return RunRequest()

    return weekly_cleanup


def monthly_repack_schedule(repack_job: JobDefinition | UnresolvedAssetJobDefinition) -> ScheduleDefinition:
    """First Sunday of the month at 4 AM Europe/Zurich — after the weekly cleanup completes."""

    @schedule(cron_schedule="0 4 * * 0", job=repack_job, execution_timezone="Europe/Zurich")
    def monthly_repack(context: ScheduleEvaluationContext) -> RunRequest | SkipReason:
        if context.scheduled_execution_time.day > 7:
            return SkipReason("Skipping: only the first Sunday of the month triggers pg_repack.")
        return RunRequest()

    return monthly_repack
