import asyncio
import logging
import time
from datetime import UTC, datetime, timedelta

from bson import ObjectId
from pydantic import ValidationError
from redis.asyncio import Redis

from swiss_ai_hub.core.agents.agent_config import CRON_CONFIG_KEY
from swiss_ai_hub.core.distributor.events.external_agent_event import ExternalAgentEvent
from swiss_ai_hub.core.distributor.external_agent_event_distributor import ExternalAgentEventDistributor
from swiss_ai_hub.core.events.agent.control.start.cron_start_event import CronStartEvent
from swiss_ai_hub.core.persistence.agents.agent_class_entity import AgentClassEntity
from swiss_ai_hub.core.persistence.agents.agent_config_entity_document import AgentConfigEntityDocument
from swiss_ai_hub.core.persistence.messaging.entities.thread_entity import AgentInstanceRef, ThreadEntity
from swiss_ai_hub.core.scheduling.cron_schedule import CronSchedule
from swiss_ai_hub.core.scheduling.cron_schedule_calculator import CronScheduleCalculator
from swiss_ai_hub.core.scheduling.schedule_state_store import ScheduleStateStore

logger = logging.getLogger(__name__)

_SCHEDULED_THREAD_NAME = "Scheduled runs"


class CronScheduler:
    """Fires cron-scheduled agent runs, as a singleton across however many replicas host it.

    Runs are system runs: the thread has no members and the start event carries no user, so nothing
    downstream can mistake a scheduled run for one a person initiated. Everything the agent needs to
    know about its tenant already lives on its own profile.

    The service holds no state of its own — leadership, watermark, and occurrence claims all live in
    Redis via `ScheduleStateStore`, so it can be lifted out of the API into `aihub-daemon` unchanged.

    The schedule is read from `config_data[CRON_CONFIG_KEY]`, a platform-owned field on `AgentConfig`
    that `AgentRunner` populates for schedulable classes. A blueprint therefore cannot mis-name it, so
    there is no reconciling to do between "advertised as schedulable" and "has a readable schedule".
    """

    def __init__(
        self,
        *,
        redis: Redis,
        external_agent_event_distributor: ExternalAgentEventDistributor,
        tick_interval: int = 30,
        lease_ttl: int = 120,
        max_catchup: timedelta = timedelta(minutes=15),
    ) -> None:
        self._distributor = external_agent_event_distributor
        self._tick_interval = tick_interval
        self._lease_ttl = lease_ttl
        self._max_catchup = max_catchup
        # Claims must outlive the catch-up window, or an occurrence dropped from a replayed window
        # could be claimed a second time after its key expired.
        self._store = ScheduleStateStore(
            redis=redis,
            lease_ttl=lease_ttl,
            claim_ttl=int(max_catchup.total_seconds()) * 4,
        )
        self.running: bool = False
        self.task: asyncio.Task | None = None

    def start(self) -> bool:
        """Starts the scheduling loop, returning False if it was already running.

        Synchronous, unlike `stop`, because scheduling a task is not itself an awaitable operation and
        an `async def` with nothing to await only claims otherwise. It must still be called from a
        running event loop — `asyncio.create_task` says so if it is not.
        """
        if self.running:
            logger.warning("Cron scheduler is already running")
            return False

        self.running = True
        self.task = asyncio.create_task(self._scheduling_loop())
        logger.info("Cron scheduler started")
        return True

    async def stop(self) -> bool:
        if not self.running:
            logger.warning("Cron scheduler is not running")
            return False

        self.running = False
        if self.task:
            self.task.cancel()
            await asyncio.gather(self.task, return_exceptions=True)
        logger.info("Cron scheduler stopped")
        return True

    async def _scheduling_loop(self) -> None:
        while self.running:
            try:
                await self._tick()
            except Exception as error:
                logger.exception(f"Error in scheduler tick: {error}")

            await asyncio.sleep(self._tick_interval)

    async def _tick(self) -> None:
        """Fires every occurrence that fell due since the last completed tick."""
        async with self._store.leadership() as is_leader:
            if not is_leader:
                return

            now = datetime.now(UTC)
            watermark = await self._store.get_watermark()
            if watermark is None:
                # Cold start: adopt the current time rather than firing everything a schedule would
                # have produced since the epoch. The next tick covers the first real window.
                await self._store.set_watermark(now)
                logger.info("Scheduler watermark initialised; first window starts from now")
                return

            self._warn_if_clock_is_behind_watermark(watermark, now)

            started = time.monotonic()
            window_start = self._clamp_window_start(watermark, now)
            for schedule, config in self._due_instances():
                await self._fire_occurrences(schedule, config, window_start, now)
            self._warn_about_occurrences_dropped_while_offline(window_start, now)

            await self._store.set_watermark(now)
            self._warn_if_tick_outran_its_lease(time.monotonic() - started)

    @staticmethod
    def _warn_if_clock_is_behind_watermark(watermark: datetime, now: datetime) -> None:
        """Surfaces a watermark that sits in this replica's future, which otherwise fires nothing silently.

        The watermark is wall-clock, so a replica whose clock runs fast writes one ahead of real time.
        Every replica then computes an inverted window and fires nothing at all until the clock catches
        up — no error, no empty-result signal, just silence. The system does repair itself once a
        correctly-clocked replica writes the next watermark, which is precisely why the watermark is
        left free to move backwards; this warning is what makes the interim visible.
        """
        if now >= watermark:
            return

        logger.warning(
            "Scheduler watermark %s is ahead of this replica's clock (%s) by %s — nothing will fire "
            "until the clock passes it. Check for clock skew between replicas.",
            watermark.isoformat(),
            now.isoformat(),
            watermark - now,
        )

    def _warn_if_tick_outran_its_lease(self, duration_seconds: float) -> None:
        """Surfaces a tick that ran longer than its lease, which lets a second replica tick concurrently.

        No run is duplicated when that happens — the per-occurrence claims hold — but the two replicas
        write watermarks out of order, so the next tick re-scans a window it already covered. Wasted
        work rather than a fault, and worth knowing about because a tick is normally sub-second.
        """
        if duration_seconds < self._lease_ttl:
            return

        logger.warning(
            "Scheduler tick took %.1fs, outrunning its %ss lease — another replica may have ticked "
            "concurrently and the watermark may have moved backwards. Runs are still fired exactly "
            "once; the next tick will re-scan an already-covered window.",
            duration_seconds,
            self._lease_ttl,
        )

    def _clamp_window_start(self, watermark: datetime, now: datetime) -> datetime:
        """Bounds how far back a tick replays, so downtime does not produce a burst of stale runs."""
        earliest = now - self._max_catchup
        if watermark >= earliest:
            return watermark

        logger.warning(
            "Scheduler was behind by %s; skipping occurrences older than the %s catch-up window",
            now - watermark,
            self._max_catchup,
        )
        return earliest

    def _due_instances(self) -> list[tuple[CronSchedule, AgentConfigEntityDocument]]:
        """Profiles of online schedulable classes that carry a schedule, paired with that schedule."""
        schedulable_entities = AgentClassEntity.get_online_schedulable()
        if not schedulable_entities:
            return []

        return self._scheduled_profiles([entity.agent_class for entity in schedulable_entities])

    @staticmethod
    def _scheduled_profiles(agent_classes: list[str]) -> list[tuple[CronSchedule, AgentConfigEntityDocument]]:
        """Profiles of the given classes that carry a parseable schedule, paired with that schedule."""
        instances: list[tuple[CronSchedule, AgentConfigEntityDocument]] = []
        for config in AgentConfigEntityDocument.find_for_classes(agent_classes):
            raw_schedule = (config.config_data or {}).get(CRON_CONFIG_KEY)
            if not raw_schedule:
                continue
            # Deliberately not fail-fast. The profile store is shared, and the config save path
            # validates against a generated JSON-schema model that cannot carry CronSchedule's cron
            # and timezone validators — so a malformed schedule can reach storage. Letting it raise
            # here would abort the tick before the watermark advanced, and every subsequent tick would
            # rediscover the same row: one bad profile would permanently starve every other schedule.
            try:
                schedule = CronSchedule.model_validate(raw_schedule)
            except ValidationError:
                logger.exception(
                    "Skipping %s/%s: stored schedule is not valid",
                    config.agent_class,
                    config.agent_id,
                )
                continue
            instances.append((schedule, config))
        return instances

    @classmethod
    def _warn_about_occurrences_dropped_while_offline(cls, window_start: datetime, now: datetime) -> None:
        """Reports the occurrences this tick passed over because the blueprint had no runner online.

        Dropping them is the intended behaviour — the scheduler does not queue work for an agent that
        cannot consume it, and a run whose moment has passed is rarely worth firing late. But the
        watermark advances either way, so they are gone rather than deferred, and silence made that
        indistinguishable from a schedule that simply had nothing due.

        Not rate-limited, unlike the misnamed-field warning: every line here reports distinct work that
        was actually lost, and its frequency is the schedule's own, not the tick's.
        """
        offline_entities = AgentClassEntity.get_offline_schedulable()
        if not offline_entities:
            return

        last_seen = {entity.agent_class: entity.last_discovered for entity in offline_entities}
        for schedule, config in cls._scheduled_profiles(list(last_seen)):
            dropped = CronScheduleCalculator.occurrences_between(schedule, window_start, now)
            if not dropped:
                continue
            logger.warning(
                "Skipped %d occurrence(s) for %s/%s — class offline since %s",
                len(dropped),
                config.agent_class,
                config.agent_id,
                last_seen[config.agent_class],
            )

    async def _fire_occurrences(
        self,
        schedule: CronSchedule,
        config: AgentConfigEntityDocument,
        window_start: datetime,
        now: datetime,
    ) -> None:
        for occurrence in CronScheduleCalculator.occurrences_between(schedule, window_start, now):
            if not await self._store.claim_occurrence(config.agent_class, config.agent_id, occurrence):
                logger.debug(
                    "Occurrence %s for %s/%s already claimed",
                    occurrence.isoformat(),
                    config.agent_class,
                    config.agent_id,
                )
                continue
            await self._start_run(config, occurrence)

    async def _start_run(self, config: AgentConfigEntityDocument, occurrence: datetime) -> None:
        """Publishes a scheduled start event on the normal agent control path."""
        agent = AgentInstanceRef(agent_class=config.agent_class, agent_id=config.agent_id)
        thread = ThreadEntity.get_or_create_scheduled_thread(_SCHEDULED_THREAD_NAME, agent)

        external_event = ExternalAgentEvent(
            thread_id=str(thread.id),
            display_id=str(ObjectId()),
            event=CronStartEvent(scheduled_for=occurrence),
        )
        await self._distributor.distribute_event(external_event, user=None, target_agent=agent)

        logger.info(
            "Started scheduled run for %s/%s (occurrence %s, thread %s)",
            config.agent_class,
            config.agent_id,
            occurrence.isoformat(),
            thread.id,
        )
