from datetime import datetime

import dagster as dg
from dagster import job, op

from aihub_backup.dagster.schedules.factory import daily_backup_schedule


@op
def _noop() -> None:
    pass


@job(name="test_backup_job")
def _test_job() -> None:
    _noop()


def test_daily_backup_schedule_produces_run_request() -> None:
    """Schedule produces a RunRequest."""
    schedule = daily_backup_schedule(_test_job)

    scheduled_time = datetime(2026, 2, 19, 2, 0, 0)
    context = dg.build_schedule_context(scheduled_execution_time=scheduled_time)

    result = schedule(context)

    assert isinstance(result, dg.RunRequest)


def test_daily_backup_schedule_has_no_run_config() -> None:
    """Schedule produces a RunRequest with no custom run config."""
    schedule = daily_backup_schedule(_test_job)

    scheduled_time = datetime(2026, 2, 19, 2, 0, 0)
    context = dg.build_schedule_context(scheduled_execution_time=scheduled_time)

    result = schedule(context)

    assert result.run_config in (None, {})
