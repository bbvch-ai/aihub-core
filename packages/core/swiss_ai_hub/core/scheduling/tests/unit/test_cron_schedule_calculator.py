from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from swiss_ai_hub.core.scheduling.cron_schedule import CronSchedule
from swiss_ai_hub.core.scheduling.cron_schedule_calculator import CronScheduleCalculator

_ZURICH = ZoneInfo("Europe/Zurich")
_EVERY_DAY = {"day_of_month": "*", "month": "*", "day_of_week": "*"}
_HOURLY = CronSchedule(minute="0", hour="*", **_EVERY_DAY)
_DAILY_NOON_ZURICH = CronSchedule(minute="0", hour="12", timezone="Europe/Zurich", **_EVERY_DAY)


def _utc(year: int, month: int, day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=UTC)


class TestOccurrencesBetween:
    def test_returns_every_occurrence_in_the_window(self):
        occurrences = CronScheduleCalculator.occurrences_between(
            _HOURLY, _utc(2026, 8, 11, 10, 30), _utc(2026, 8, 11, 13, 30)
        )
        assert occurrences == [_utc(2026, 8, 11, 11), _utc(2026, 8, 11, 12), _utc(2026, 8, 11, 13)]

    def test_window_is_open_at_the_start(self):
        """The previous tick's watermark is the new window start, so an occurrence exactly on it
        already fired and must not fire again."""
        occurrences = CronScheduleCalculator.occurrences_between(_HOURLY, _utc(2026, 8, 11, 12), _utc(2026, 8, 11, 13))
        assert occurrences == [_utc(2026, 8, 11, 13)]

    def test_window_is_closed_at_the_end(self):
        occurrences = CronScheduleCalculator.occurrences_between(
            _HOURLY, _utc(2026, 8, 11, 11, 30), _utc(2026, 8, 11, 12)
        )
        assert occurrences == [_utc(2026, 8, 11, 12)]

    def test_returns_empty_when_nothing_is_due(self):
        assert (
            CronScheduleCalculator.occurrences_between(_HOURLY, _utc(2026, 8, 11, 12, 1), _utc(2026, 8, 11, 12, 59))
            == []
        )

    def test_converts_local_schedule_to_utc(self):
        """Noon in Zurich is 10:00 UTC in summer — the caller only ever deals in UTC."""
        occurrences = CronScheduleCalculator.occurrences_between(
            _DAILY_NOON_ZURICH, _utc(2026, 8, 11, 0), _utc(2026, 8, 12, 23)
        )
        assert occurrences == [_utc(2026, 8, 11, 10), _utc(2026, 8, 12, 10)]


class TestDaylightSavingTime:
    def test_daily_schedule_keeps_its_wall_clock_time_across_the_spring_shift(self):
        """Zurich springs forward on 2026-03-29. "Every day at 12:00" must stay 12:00 local, which
        means the UTC instant moves by an hour — the reason occurrences are computed in the local zone."""
        occurrences = CronScheduleCalculator.occurrences_between(
            _DAILY_NOON_ZURICH, _utc(2026, 3, 28, 0), _utc(2026, 3, 30, 23)
        )

        local_times = [occurrence.astimezone(_ZURICH) for occurrence in occurrences]
        assert [local.hour for local in local_times] == [12, 12, 12]
        assert [local.utcoffset().total_seconds() / 3600 for local in local_times] == [1, 2, 2]

    def test_daily_schedule_keeps_its_wall_clock_time_across_the_autumn_shift(self):
        occurrences = CronScheduleCalculator.occurrences_between(
            _DAILY_NOON_ZURICH, _utc(2026, 10, 24, 0), _utc(2026, 10, 26, 23)
        )

        local_times = [occurrence.astimezone(_ZURICH) for occurrence in occurrences]
        assert [local.hour for local in local_times] == [12, 12, 12]
        assert [local.utcoffset().total_seconds() / 3600 for local in local_times] == [2, 1, 1]


class TestNextOccurrence:
    def test_returns_the_first_occurrence_strictly_after(self):
        assert CronScheduleCalculator.next_occurrence(_HOURLY, _utc(2026, 8, 11, 12)) == _utc(2026, 8, 11, 13)


class TestCountBetween:
    """For a caller that wants the number over a span it does not control, so materialising the list is
    not an option — the clamp counts what it discarded, and that span is a whole outage."""

    def test_agrees_with_enumerating_the_window(self):
        counted = CronScheduleCalculator.count_between(_HOURLY, _utc(2026, 8, 11, 0), _utc(2026, 8, 11, 12), 100)

        assert counted == len(
            CronScheduleCalculator.occurrences_between(_HOURLY, _utc(2026, 8, 11, 0), _utc(2026, 8, 11, 12))
        )

    def test_stops_at_the_limit_rather_than_at_the_end_of_the_window(self):
        assert CronScheduleCalculator.count_between(_HOURLY, _utc(2026, 8, 11, 0), _utc(2027, 8, 11, 0), 5) == 5

    def test_counts_nothing_in_an_empty_window(self):
        assert CronScheduleCalculator.count_between(_HOURLY, _utc(2026, 8, 11, 12), _utc(2026, 8, 11, 12), 100) == 0


class TestRunsPerMonth:
    """What makes a schedule's cost knowable while an admin is still typing it."""

    def test_counts_the_tightest_expressible_schedule(self):
        every_minute = CronSchedule(minute="*", hour="*", **_EVERY_DAY)

        assert CronScheduleCalculator.runs_per_month(every_minute, 100_000) == 30 * 24 * 60

    def test_counts_an_hourly_schedule(self):
        assert CronScheduleCalculator.runs_per_month(_HOURLY, 100_000) == 720

    def test_the_answer_does_not_depend_on_when_it_is_asked(self):
        """The number is compared against a configured ceiling, so a window anchored to "now" would
        reject in February what it allowed in January."""
        first = CronScheduleCalculator.runs_per_month(_HOURLY, 100_000)
        second = CronScheduleCalculator.runs_per_month(_HOURLY, 100_000)

        assert first == second == 720

    def test_respects_the_limit(self):
        assert CronScheduleCalculator.runs_per_month(_HOURLY, 10) == 10

    def test_a_schedule_rarer_than_the_window_can_count_zero(self):
        """The harmless direction for a maximum — a monthly schedule is never what a ceiling is for."""
        monthly = CronSchedule(minute="0", hour="3", day_of_month="31", month="*", day_of_week="*")

        assert CronScheduleCalculator.runs_per_month(monthly, 100_000) == 0
