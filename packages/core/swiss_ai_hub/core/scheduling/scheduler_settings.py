from datetime import timedelta
from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.scheduling.schedule_state_store import DEFAULT_KEY_PREFIX
from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings

# The most runs any cron expression can produce in the 30-day probe window: the minute is cron's finest
# position, so every-minute is the ceiling of what a schedule can ask for.
MINUTES_PER_MONTH = 30 * 24 * 60


class SchedulerSettings(EnvironmentSettings):
    """Operational knobs for the cron scheduler.

    These were constructor defaults, which put every one of them behind a deploy. Tick pacing and the
    catch-up horizon are the levers an operator reaches for when a schedule misbehaves, and retention is
    per-environment by nature — a staging box wants a much shorter history than production.

    The prefix is `SCHEDULER_`, not the service's own name, so the variables survive a rename of the
    class that reads them.
    """

    model_config = EnvironmentSettings.create_settings_config("SCHEDULER_")

    TICK_INTERVAL_SECONDS: Annotated[
        int,
        Field(ge=1, description="Seconds between scheduler ticks. Bounds how late an occurrence can fire."),
    ] = 30
    LEASE_TTL_SECONDS: Annotated[
        int,
        Field(
            ge=1,
            description="Leader-lease lifetime. Must exceed the worst-case tick runtime, or the lease "
            "expires mid-tick and a second replica starts one concurrently.",
        ),
    ] = 120
    MAX_CATCHUP_MINUTES: Annotated[
        int,
        Field(
            # Zero would make the occurrence-claim TTL zero too, and `SET ... EX 0` is rejected by Redis
            # on every claim — the scheduler would stop firing entirely until the variable changed.
            ge=1,
            description="How far back a tick replays after downtime. Occurrences older than this are "
            "logged and dropped rather than fired as a burst of stale runs.",
        ),
    ] = 15
    REDIS_KEY_PREFIX: Annotated[
        str,
        Field(
            min_length=1,
            description="Namespace for all scheduler keys in Redis. Change it to run an isolated scheduler.",
        ),
    ] = DEFAULT_KEY_PREFIX
    EVENT_RETENTION_DAYS: Annotated[
        int,
        Field(
            # The one knob where zero is meaningful rather than broken: it means "off".
            ge=0,
            description="Age beyond which events in a scheduled thread are pruned. Zero disables pruning "
            "entirely, which is the default: deleting a tenant's history must be something an operator "
            "turned on, never something a deploy started doing.",
        ),
    ] = 0
    RETENTION_INTERVAL_SECONDS: Annotated[
        int,
        Field(
            ge=1,
            description="Minimum seconds between prunes, enforced cluster-wide. Keeps bulk deletes off the tick.",
        ),
    ] = 3600
    MAX_RUNS_PER_PROFILE_PER_MONTH: Annotated[
        int,
        Field(
            ge=1,
            description="Most runs a single schedule may produce in 30 days, rejected when the profile is "
            "saved. Defaults to the tightest schedule cron can express (every minute), so out of the box "
            "it rejects nothing expressible and exists for a deployment that wants to allow less.",
        ),
    ] = MINUTES_PER_MONTH
    MAX_TOTAL_RUNS_PER_MONTH: Annotated[
        int,
        Field(
            # Off by default for the same reason retention is: a bound that can reject an admin's save has
            # to be something an operator chose, never something a deploy started doing.
            ge=0,
            description="Most runs all schedules together may produce in 30 days, checked when a profile "
            "is saved. Zero disables the check, which is the default — the right ceiling depends on how "
            "many agents a deployment runs and what they cost, and no platform-wide constant knows that.",
        ),
    ] = 0

    @property
    def max_catchup(self) -> timedelta:
        return timedelta(minutes=self.MAX_CATCHUP_MINUTES)

    @property
    def max_total_runs_per_month(self) -> int | None:
        """The aggregate ceiling, or None when the check is disabled."""
        return self.MAX_TOTAL_RUNS_PER_MONTH or None

    @property
    def enforced_profile_ceiling(self) -> int | None:
        """The per-profile ceiling, or None when no expressible schedule could reach it.

        At the default nothing can exceed it, because every-minute is cron's maximum — so the check has
        no verdict to reach and counting is pure waste. It is not cheap waste either: confirming an
        every-minute schedule is *within* a 43,200 ceiling means stepping croniter 43,200 times, about
        half a second, which the scan-side check would otherwise pay per such profile on every tick.
        """
        return self.MAX_RUNS_PER_PROFILE_PER_MONTH if self.MAX_RUNS_PER_PROFILE_PER_MONTH < MINUTES_PER_MONTH else None

    @property
    def event_retention(self) -> timedelta | None:
        """The retention window, or None when pruning is disabled."""
        return timedelta(days=self.EVENT_RETENTION_DAYS) if self.EVENT_RETENTION_DAYS > 0 else None
