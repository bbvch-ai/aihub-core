from datetime import UTC, datetime

from croniter import croniter

from swiss_ai_hub.core.scheduling.agent_schedule import AgentSchedule


class CronScheduleCalculator:
    """Computes which cron occurrences of a schedule fall inside a time window.

    The scheduler works in windows rather than asking "is it due right now?" because ticks are periodic:
    an occurrence between two ticks would otherwise be missed entirely. Occurrences are enumerated in the
    schedule's own timezone so DST shifts move them with the wall clock, then returned in UTC, which is
    the only form the rest of the platform stores or compares.
    """

    @staticmethod
    def occurrences_between(
        schedule: AgentSchedule,
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
    def next_occurrence(schedule: AgentSchedule, after: datetime) -> datetime:
        """The first occurrence strictly after `after`, in UTC."""
        local_after = after.astimezone(schedule.zone_info)
        return croniter(schedule.expression, local_after).get_next(datetime).astimezone(UTC)
