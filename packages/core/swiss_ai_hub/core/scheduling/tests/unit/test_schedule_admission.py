"""Admission control for schedules: rejecting the cost at save time rather than metering it later.

A cron expression is a declaration, so how much work it produces is knowable before the first run. These
tests pin the two ceilings and, just as importantly, pin that neither of them rejects anything by default.
"""

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from swiss_ai_hub.core.scheduling.cron_schedule import CronSchedule
from swiss_ai_hub.core.scheduling.schedule_admission import ScheduleAdmission
from swiss_ai_hub.core.scheduling.scheduler_settings import SchedulerSettings

_MODULE = "swiss_ai_hub.core.scheduling.schedule_admission"
_EVERY_MINUTE = {"minute": "*", "hour": "*", "day_of_month": "*", "month": "*", "day_of_week": "*", "timezone": "UTC"}
_HOURLY = {**_EVERY_MINUTE, "minute": "0"}
_DAILY = {**_HOURLY, "hour": "3"}


def _schedule(raw: dict) -> CronSchedule:
    return CronSchedule.model_validate(raw)


def _stored(agent_id: str, raw: dict | None = None, agent_class: str = "CronDemoAgent"):
    return SimpleNamespace(agent_class=agent_class, agent_id=agent_id, config_data={"cron": raw or _HOURLY})


def _reject(schedule: CronSchedule, settings: SchedulerSettings, stored: list | None = None) -> str | None:
    with patch(f"{_MODULE}.AgentConfigEntityDocument.find_with_config_key", return_value=stored or []):
        return ScheduleAdmission.rejection_reason(schedule, "CronDemoAgent", "demo", settings)


class TestTheDefaultsRejectNothing:
    """The review this replaced landed on a platform-wide constant that was simultaneously too low to
    allow a supported schedule and too high to signal a broken scheduler. A default that rejects nothing
    cannot repeat that: an operator picks the number for their own deployment, or there is no number."""

    def test_every_minute_is_admissible_out_of_the_box(self) -> None:
        """The tightest schedule cron can express is supported, so the default must not refuse it."""
        assert _reject(_schedule(_EVERY_MINUTE), SchedulerSettings()) is None

    def test_the_aggregate_check_is_off_by_default(self) -> None:
        already_running = [_stored(str(index), _EVERY_MINUTE) for index in range(50)]

        assert _reject(_schedule(_EVERY_MINUTE), SchedulerSettings(), already_running) is None


class TestThePerProfileCeiling:
    def test_rejects_a_schedule_over_the_configured_ceiling(self) -> None:
        """Hourly is 720 runs in 30 days, so a ceiling of 500 refuses it."""
        settings = SchedulerSettings(MAX_RUNS_PER_PROFILE_PER_MONTH=500)

        rejection = _reject(_schedule(_HOURLY), settings)

        assert rejection is not None
        assert "500" in rejection

    def test_admits_a_schedule_exactly_at_the_ceiling(self) -> None:
        """Hourly is 720 runs in 30 days, so a ceiling of 720 is a bound rather than an off-by-one."""
        assert _reject(_schedule(_HOURLY), SchedulerSettings(MAX_RUNS_PER_PROFILE_PER_MONTH=720)) is None

    def test_names_the_problem_rather_than_the_mechanism(self) -> None:
        """The message reaches an admin looking at a form, which is the whole point of checking here."""
        rejection = _reject(_schedule(_EVERY_MINUTE), SchedulerSettings(MAX_RUNS_PER_PROFILE_PER_MONTH=100))

        assert "runs more than 100 times per 30 days" in rejection


class TestTheAggregateCeiling:
    """400 hourly profiles are 288,000 runs a month and every one of those configs is unremarkable on its
    own. The total is the only place that configuration is visible."""

    def test_rejects_a_schedule_that_pushes_the_total_over(self) -> None:
        """Two hourly profiles already stored is 1440; a third takes the estate to 2160 over a 2000 cap,
        and neither of the three configs looks remarkable on its own."""
        settings = SchedulerSettings(MAX_TOTAL_RUNS_PER_MONTH=2000)
        already_running = [_stored("a"), _stored("b")]

        rejection = _reject(_schedule(_HOURLY), settings, already_running)

        assert rejection is not None
        assert "2160" in rejection
        assert "1440 are already scheduled elsewhere" in rejection

    def test_a_truncated_total_is_reported_as_a_floor(self) -> None:
        """Counting stops at the ceiling, so the figure past it is a lower bound. Printing it as exact
        would understate a large estate by an order of magnitude."""
        settings = SchedulerSettings(MAX_TOTAL_RUNS_PER_MONTH=100)
        estate = [_stored(str(index), _EVERY_MINUTE) for index in range(50)]

        rejection = _reject(_schedule(_HOURLY), settings, estate)

        assert "at least" in rejection

    def test_admits_when_the_total_still_fits(self) -> None:
        settings = SchedulerSettings(MAX_TOTAL_RUNS_PER_MONTH=1000)

        assert _reject(_schedule(_DAILY), settings, [_stored("a", _DAILY)]) is None

    def test_a_profile_is_not_counted_against_itself(self) -> None:
        """Otherwise the first edit of a profile sitting near the ceiling could never be saved again,
        because its own current schedule would be counted alongside its replacement."""
        settings = SchedulerSettings(MAX_TOTAL_RUNS_PER_MONTH=800)
        stored_self = _stored("demo", _HOURLY)

        assert _reject(_schedule(_HOURLY), settings, [stored_self]) is None

    def test_an_unscheduled_profile_contributes_nothing(self) -> None:
        settings = SchedulerSettings(MAX_TOTAL_RUNS_PER_MONTH=800)
        blank = _stored("a", {key: "" for key in _HOURLY})

        assert _reject(_schedule(_HOURLY), settings, [blank]) is None

    def test_a_stored_row_that_cannot_be_parsed_does_not_block_every_save(self) -> None:
        """A row predating this validation is a reason to undercount, never a reason to refuse writes
        until somebody finds it."""
        settings = SchedulerSettings(MAX_TOTAL_RUNS_PER_MONTH=800)
        broken = _stored("a", {**_HOURLY, "minute": "99"})

        assert _reject(_schedule(_HOURLY), settings, [broken]) is None


class TestTheCountingIsBounded:
    """Same discipline as the clamp's drop count: once the verdict cannot change, counting on only makes
    the rejection slower to reach — and this one runs while an admin waits on an HTTP response."""

    def test_counting_stops_once_the_ceiling_is_passed(self) -> None:
        settings = SchedulerSettings(MAX_TOTAL_RUNS_PER_MONTH=10)
        estate = [_stored(str(index), _EVERY_MINUTE) for index in range(500)]

        with patch(f"{_MODULE}.AgentConfigEntityDocument.find_with_config_key", return_value=estate):
            with patch(f"{_MODULE}.CronScheduleCalculator.runs_per_month", side_effect=[11, 11]) as runs_per_month:
                ScheduleAdmission.rejection_reason(_schedule(_HOURLY), "CronDemoAgent", "demo", settings)

        # Once for the schedule being saved, once for the first stored profile — which already passed it.
        assert runs_per_month.call_count == 2


@pytest.mark.parametrize(
    ("raw", "expected"),
    [(_EVERY_MINUTE, 43_200), (_HOURLY, 720), ({**_HOURLY, "minute": "*/5"}, 8_640), (_DAILY, 30)],
)
def test_runs_per_month_matches_the_schedule(raw: dict, expected: int) -> None:
    """Pinned because the two ceilings are meaningless if the number they compare against drifts."""
    from swiss_ai_hub.core.scheduling.cron_schedule_calculator import CronScheduleCalculator

    assert CronScheduleCalculator.runs_per_month(_schedule(raw), 100_000) == expected


class TestAnUnreachableCeilingCostsNothing:
    """Confirming an every-minute schedule sits within the default 43,200 means 43,200 croniter steps —
    half a second, spent to reach an answer that was never in doubt. On the scan side that is paid per
    such profile on every tick; on the save side it is paid inside the request an admin is waiting on."""

    def test_nothing_is_counted_when_no_ceiling_can_reject(self) -> None:
        with patch(f"{_MODULE}.CronScheduleCalculator.runs_per_month") as counted:
            assert _reject(_schedule(_EVERY_MINUTE), SchedulerSettings()) is None

        counted.assert_not_called()

    def test_counting_resumes_once_a_ceiling_is_enforced(self) -> None:
        settings = SchedulerSettings(MAX_RUNS_PER_PROFILE_PER_MONTH=500)

        with patch(f"{_MODULE}.CronScheduleCalculator.runs_per_month", return_value=501) as counted:
            assert _reject(_schedule(_HOURLY), settings) is not None

        counted.assert_called_once()

    def test_the_aggregate_ceiling_alone_is_enough_to_count(self) -> None:
        """The per-profile default is unreachable, but the total is not — so the schedule still has to be
        measured to know what it contributes."""
        settings = SchedulerSettings(MAX_TOTAL_RUNS_PER_MONTH=100)

        assert _reject(_schedule(_HOURLY), settings) is not None
