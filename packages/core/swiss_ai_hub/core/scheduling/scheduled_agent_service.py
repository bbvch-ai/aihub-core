import asyncio
import logging
from datetime import UTC, datetime, timedelta

from bson import ObjectId
from redis.asyncio import Redis

from swiss_ai_hub.core.distributor.events.external_agent_event import ExternalAgentEvent
from swiss_ai_hub.core.distributor.external_agent_event_distributor import ExternalAgentEventDistributor
from swiss_ai_hub.core.events.agent.control.start.scheduled_start_event import ScheduledStartEvent
from swiss_ai_hub.core.persistence.agents.agent_class_entity import AgentClassEntity
from swiss_ai_hub.core.persistence.agents.agent_config_entity_document import AgentConfigEntityDocument
from swiss_ai_hub.core.persistence.messaging.entities.thread_entity import AgentInstanceRef, ThreadEntity
from swiss_ai_hub.core.scheduling.agent_schedule import AgentSchedule
from swiss_ai_hub.core.scheduling.cron_schedule_calculator import CronScheduleCalculator
from swiss_ai_hub.core.scheduling.schedule_state_store import ScheduleStateStore

logger = logging.getLogger(__name__)

SCHEDULE_CONFIG_KEY = "schedule"
_SCHEDULED_THREAD_NAME = "scheduled"


class ScheduledAgentService:
    """Fires cron-scheduled agent runs, as a singleton across however many replicas host it.

    Runs are system runs: the thread has no members and the start event carries no user, so nothing
    downstream can mistake a scheduled run for one a person initiated. Everything the agent needs to
    know about its tenant already lives on its own profile.

    The service holds no state of its own — leadership, watermark, and occurrence claims all live in
    Redis via `ScheduleStateStore`, so it can be lifted out of the API into `aihub-daemon` unchanged.
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

    async def start(self) -> bool:
        if self.running:
            logger.warning("Scheduled agent service is already running")
            return False

        self.running = True
        self.task = asyncio.create_task(self._scheduling_loop())
        logger.info("Scheduled agent service started")
        return True

    async def stop(self) -> bool:
        if not self.running:
            logger.warning("Scheduled agent service is not running")
            return False

        self.running = False
        if self.task:
            self.task.cancel()
            await asyncio.gather(self.task, return_exceptions=True)
        logger.info("Scheduled agent service stopped")
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

            window_start = self._clamp_window_start(watermark, now)
            for schedule, config in self._due_instances():
                await self._fire_occurrences(schedule, config, window_start, now)

            await self._store.set_watermark(now)

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

    @staticmethod
    def _due_instances() -> list[tuple[AgentSchedule, AgentConfigEntityDocument]]:
        """Profiles of online schedulable classes that carry a schedule, paired with that schedule."""
        schedulable_classes = [entity.agent_class for entity in AgentClassEntity.get_online_schedulable()]
        if not schedulable_classes:
            return []

        instances: list[tuple[AgentSchedule, AgentConfigEntityDocument]] = []
        for config in AgentConfigEntityDocument.find_for_classes(schedulable_classes):
            raw_schedule = (config.config_data or {}).get(SCHEDULE_CONFIG_KEY)
            if not raw_schedule:
                continue
            instances.append((AgentSchedule.model_validate(raw_schedule), config))
        return instances

    async def _fire_occurrences(
        self,
        schedule: AgentSchedule,
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
        thread = ThreadEntity.create_thread(_SCHEDULED_THREAD_NAME, users=[], agents=[agent])

        external_event = ExternalAgentEvent(
            thread_id=str(thread.id),
            display_id=str(ObjectId()),
            event=ScheduledStartEvent(scheduled_for=occurrence),
        )
        await self._distributor.distribute_event(external_event, user=None, target_agent=agent)

        logger.info(
            "Started scheduled run for %s/%s (occurrence %s, thread %s)",
            config.agent_class,
            config.agent_id,
            occurrence.isoformat(),
            thread.id,
        )
