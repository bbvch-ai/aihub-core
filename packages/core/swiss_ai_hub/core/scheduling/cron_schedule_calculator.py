from datetime import UTC, datetime, timedelta

from croniter import croniter

from swiss_ai_hub.core.scheduling.cron_schedule import CronSchedule

# A fixed anchor for `runs_per_month`, chosen to contain a 31st and both DST shifts' absence, so the
# probe window is an ordinary month rather than an unusual one. It must never move: the answer is
# compared against a configured ceiling, and an anchor that drifted would make the same expression
# accepted one day and rejected the next.
_PROBE_WINDOW_START = datetime(2026, 1, 1, tzinfo=UTC)


class CronScheduleCalculator:
    """Computes which cron occurrences of a schedule fall inside a time window.

    The scheduler works in windows rather than asking "is it due right now?" because ticks are periodic:
    an occurrence between two ticks would otherwise be missed entirely. Occurrences are enumerated in the
    schedule's own timezone so DST shifts move them with the wall clock, then returned in UTC, which is
    the only form the rest of the platform stores or compares.
    """

    @staticmethod
    def occurrences_between(
        schedule: CronSchedule,
        after: datetime,
        until: datetime,
    ) -> list[datetime]:
        """Occurrences in `(after, until]`, in UTC and ascending order.

        The window is half-open at the start so an occurrence already fired on the previous tick — whose
        timestamp became the new watermark — is not returned a second time.
        """
        local_after = after.astimezone(schedule.zone_info)
        cron = croniter(schedule.expression, local_after)

        occurrences: list[datetime] = []
        while True:
            occurrence = cron.get_next(datetime).astimezone(UTC)
            if occurrence > until:
                return occurrences
            occurrences.append(occurrence)

    @staticmethod
    def count_between(schedule: CronSchedule, after: datetime, until: datetime, limit: int) -> int:
        """How many occurrences fall in `(after, until]`, counted up to `limit` and no further.

        For a caller that wants the number rather than the occurrences themselves over a span it does not
        control. `occurrences_between` materialises the whole list, which is right when every element is
        about to be fired — the firing window is clamped — but ruinous over an unclamped span: a year of
        a minute-by-minute schedule is half a million datetimes built to produce one integer.

        Returning `limit` means "at least this many", so a caller that cares must say so when it reports.
        """
        cron = croniter(schedule.expression, after.astimezone(schedule.zone_info))

        counted = 0
        while counted < limit:
            if cron.get_next(datetime).astimezone(UTC) > until:
                break
            counted += 1
        return counted

    @staticmethod
    def runs_per_month(schedule: CronSchedule, limit: int) -> int:
        """How many runs this schedule produces in 30 days, counted up to `limit` and no further.

        This is what makes a schedule's cost knowable while an admin is still typing it. A cron expression
        is a declaration, not traffic: nothing about the arrival rate is unknown at the moment it is saved,
        so the question "is this too much?" is answerable then rather than discovered later by a counter.

        Thirty days rather than a calendar month, so the answer does not depend on which month it is asked
        in — the number is compared against a configured ceiling, and a ceiling that moves with February
        would reject in one month what it allowed in another. Schedules rarer than the window (`0 0 31 * *`)
        can land on zero, which is the harmless direction for a maximum.

        Anchored at a fixed instant for the same reason: two admins saving the same expression on different
        days must get the same verdict.
        """
        return CronScheduleCalculator.count_between(
            schedule, _PROBE_WINDOW_START, _PROBE_WINDOW_START + timedelta(days=30), limit
        )

    @staticmethod
    def next_occurrence(schedule: CronSchedule, after: datetime) -> datetime:
        """The first occurrence strictly after `after`, in UTC."""
        local_after = after.astimezone(schedule.zone_info)
        return croniter(schedule.expression, local_after).get_next(datetime).astimezone(UTC)
