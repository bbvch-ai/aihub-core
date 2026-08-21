from datetime import timedelta
from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.scheduling.schedule_state_store import DEFAULT_KEY_PREFIX
from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings


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
        Field(description="Seconds between scheduler ticks. Bounds how late an occurrence can fire."),
    ] = 30
    LEASE_TTL_SECONDS: Annotated[
        int,
        Field(
            description="Leader-lease lifetime. Must exceed the worst-case tick runtime, or the lease "
            "expires mid-tick and a second replica starts one concurrently."
        ),
    ] = 120
    MAX_CATCHUP_MINUTES: Annotated[
        int,
        Field(
            description="How far back a tick replays after downtime. Occurrences older than this are "
            "logged and dropped rather than fired as a burst of stale runs."
        ),
    ] = 15
    REDIS_KEY_PREFIX: Annotated[
        str,
        Field(description="Namespace for all scheduler keys in Redis. Change it to run an isolated scheduler."),
    ] = DEFAULT_KEY_PREFIX
    EVENT_RETENTION_DAYS: Annotated[
        int,
        Field(
            description="Age beyond which events in a scheduled thread are pruned. Zero disables pruning "
            "entirely, which is the default: deleting a tenant's history must be something an operator "
            "turned on, never something a deploy started doing."
        ),
    ] = 0
    RETENTION_INTERVAL_SECONDS: Annotated[
        int,
        Field(description="Minimum seconds between prunes, enforced cluster-wide. Keeps bulk deletes off the tick."),
    ] = 3600

    @property
    def max_catchup(self) -> timedelta:
        return timedelta(minutes=self.MAX_CATCHUP_MINUTES)

    @property
    def event_retention(self) -> timedelta | None:
        """The retention window, or None when pruning is disabled."""
        return timedelta(days=self.EVENT_RETENTION_DAYS) if self.EVENT_RETENTION_DAYS > 0 else None
