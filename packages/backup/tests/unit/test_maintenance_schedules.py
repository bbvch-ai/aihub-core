"""Unit tests for the maintenance schedules.

The repack schedule has a non-trivial day-of-month gate to get true
"first Sunday of the month" semantics — Vixie cron's OR semantics on
restricted day-of-month + day-of-week make ``0 4 1-7 * 0`` fire ~10×/month
rather than once. We compensate inside the schedule body via SkipReason.
"""

from __future__ import annotations

import datetime as dt

import pytest
from dagster import RunRequest, ScheduleDefinition, SkipReason, build_schedule_context, job, op

from swiss_ai_hub.backup.dagster.schedules.factory import monthly_repack_schedule, weekly_cleanup_schedule


@op
def _noop_op() -> None:
    return None


@job
def _stub_job() -> None:
    _noop_op()


def _evaluate(schedule: ScheduleDefinition, day_of_month: int) -> RunRequest | SkipReason | None:
    """Invoke the schedule body with a context fixed to a given day in May 2026."""
    ctx = build_schedule_context(
        scheduled_execution_time=dt.datetime(2026, 5, day_of_month, 4, 0, tzinfo=dt.UTC),
    )
    result = schedule.evaluate_tick(ctx)
    if result.skip_message is not None:
        return SkipReason(result.skip_message)
    if result.run_requests:
        return result.run_requests[0]
    return None


@pytest.mark.unit
def test_repack_schedule_runs_on_first_sunday() -> None:
    """May 3, 2026 is a Sunday in the first 7 days — should fire."""
    schedule = monthly_repack_schedule(_stub_job)
    result = _evaluate(schedule, day_of_month=3)
    assert isinstance(result, RunRequest)


@pytest.mark.unit
@pytest.mark.parametrize("day_of_month", [10, 17, 24, 31])
def test_repack_schedule_skips_on_subsequent_sundays(day_of_month: int) -> None:
    """All other Sundays in the month must be skipped — this is the regression
    guard for the cron OR-semantics bug. With ``0 4 1-7 * 0`` the schedule
    would fire on these days too."""
    schedule = monthly_repack_schedule(_stub_job)
    result = _evaluate(schedule, day_of_month=day_of_month)
    assert isinstance(result, SkipReason)
    assert "first Sunday" in result.skip_message


@pytest.mark.unit
def test_repack_schedule_uses_simple_weekly_cron() -> None:
    """Cron itself is just every Sunday at 04:00 — gating happens in the body."""
    schedule = monthly_repack_schedule(_stub_job)
    assert schedule.cron_schedule == "0 4 * * 0"


@pytest.mark.unit
def test_weekly_cleanup_schedule_fires_unconditionally() -> None:
    schedule = weekly_cleanup_schedule(_stub_job)
    result = _evaluate(schedule, day_of_month=15)
    assert isinstance(result, RunRequest)


@pytest.mark.unit
def test_weekly_cleanup_schedule_uses_sunday_3am_cron() -> None:
    schedule = weekly_cleanup_schedule(_stub_job)
    assert schedule.cron_schedule == "0 3 * * 0"
