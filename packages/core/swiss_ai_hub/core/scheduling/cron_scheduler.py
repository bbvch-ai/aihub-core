import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime

from bson import ObjectId
from pydantic import ValidationError
from redis.asyncio import Redis

from swiss_ai_hub.core.agents.agent_config import CRON_CONFIG_KEY
from swiss_ai_hub.core.distributor.events.external_agent_event import ExternalAgentEvent
from swiss_ai_hub.core.distributor.external_agent_event_distributor import ExternalAgentEventDistributor
from swiss_ai_hub.core.events.agent.control.start.cron_start_event import CronStartEvent
from swiss_ai_hub.core.persistence.agents.agent_class_entity import AgentClassEntity
from swiss_ai_hub.core.persistence.agents.agent_config_entity_document import AgentConfigEntityDocument
from swiss_ai_hub.core.persistence.messaging.entities.persisted_agent_event_entity import PersistedAgentEventEntity
from swiss_ai_hub.core.persistence.messaging.entities.thread_entity import AgentInstanceRef, ThreadEntity
from swiss_ai_hub.core.scheduling.cron_schedule import CronSchedule
from swiss_ai_hub.core.scheduling.cron_schedule_calculator import CronScheduleCalculator
from swiss_ai_hub.core.scheduling.schedule_state_store import ScheduleStateStore
from swiss_ai_hub.core.scheduling.scheduler_settings import SchedulerSettings

logger = logging.getLogger(__name__)

_SCHEDULED_THREAD_NAME = "Scheduled runs"

_ScheduledProfile = tuple[CronSchedule, AgentConfigEntityDocument]

# How many clamped-away occurrences a tick will count before reporting "at least N". Diagnostics must not
# be able to outrun the tick that produces them, and past a few thousand the exact figure says nothing the
# lag does not already say.
_MAX_CLAMPED_OCCURRENCES_COUNTED = 10_000


@dataclass(frozen=True)
class _SchedulableSnapshot:
    """Everything one tick needs from Mongo, read in a single pass off the event loop."""

    online: list[_ScheduledProfile] = field(default_factory=list)
    offline: list[tuple[_ScheduledProfile, datetime]] = field(default_factory=list)
    scheduled_thread_ids: list[str] = field(default_factory=list)
    # Both computed in the worker thread alongside the reads. The clamp's dropped-occurrence count spans
    # the whole downtime rather than the catch-up window — the watermark key has no TTL — so it is capped
    # to keep a tick's cost flat, and counting it on the event loop would reintroduce exactly the stall
    # the snapshot exists to remove.
    window_start: datetime | None = None
    dropped_by_clamp: int = 0


@dataclass
class _TickReport:
    """Fixed-cardinality counters for one tick, emitted as a single summary line.

    Deliberately counters rather than OTel instruments: `metrics.get_meter()` in this package resolves
    to a no-op, because the global meter provider is intentionally never set, and metrics are disabled
    by default. A summary log is what can actually be alerted on today — and it is the same instrument
    set a later migration to real counters would need, which keeps that migration mechanical.
    """

    profiles_scanned: int = 0
    occurrences_fired: int = 0
    dropped_by_clamp: int = 0
    dropped_offline: int = 0
    publish_failures: int = 0
    events_pruned: int = 0


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
        settings: SchedulerSettings | None = None,
    ) -> None:
        settings = settings or SchedulerSettings()
        self._distributor = external_agent_event_distributor
        self._settings = settings
        self._tick_interval = settings.TICK_INTERVAL_SECONDS
        self._lease_ttl = settings.LEASE_TTL_SECONDS
        self._max_catchup = settings.max_catchup
        # Claims must outlive the catch-up window, or an occurrence dropped from a replayed window
        # could be claimed a second time after its key expired.
        self._store = ScheduleStateStore(
            redis=redis,
            lease_ttl=settings.LEASE_TTL_SECONDS,
            claim_ttl=int(settings.max_catchup.total_seconds()) * 4,
            key_prefix=settings.REDIS_KEY_PREFIX,
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

            report = _TickReport()
            started = time.monotonic()

            # One hop off the event loop for every Mongo read this tick needs. These are synchronous
            # mongoengine calls in a process also serving all HTTP and WebSocket traffic, so left inline
            # they stall every request for the duration, and the stall grows with the profile count.
            # Bounded at half the lease so a slow database costs a skipped tick, not a pinned lease —
            # cancellation cannot kill the worker thread, but it does let the lease go.
            snapshot = await asyncio.wait_for(
                asyncio.to_thread(self._load_schedulable_snapshot, now, watermark),
                timeout=self._lease_ttl / 2,
            )
            report.profiles_scanned = len(snapshot.online) + len(snapshot.offline)
            report.dropped_by_clamp = snapshot.dropped_by_clamp
            window_start = snapshot.window_start
            for schedule, config in snapshot.online:
                await self._fire_occurrences(schedule, config, window_start, now, report)
            self._report_occurrences_dropped_while_offline(snapshot, window_start, now, report)

            await self._store.set_watermark(now)
            # Measured before pruning, so retention time cannot masquerade as a slow firing pass.
            self._warn_if_tick_outran_its_lease(time.monotonic() - started)

            await self._prune_scheduled_history(snapshot, now, report, time.monotonic() - started)
            self._log_tick_summary(report, time.monotonic() - started)

    def _load_schedulable_snapshot(self, now: datetime, watermark: datetime) -> _SchedulableSnapshot:
        """Reads every schedulable class and its profiles in one pass. Synchronous — runs in a thread.

        `now` is passed in rather than read here so the online/offline split uses the same instant as the
        window this tick is computing. It stays aware — `AgentClassEntity.is_online_at` owns the
        conversion to the local wall clock `last_discovered` is stored in, which is not the same as
        stripping the tzinfo off a UTC value.
        """
        entities = AgentClassEntity.get_all_schedulable()
        if not entities:
            return _SchedulableSnapshot(window_start=self._clamp_window_start(watermark, now))

        offline_last_seen = {
            entity.agent_class: entity.last_discovered
            for entity in entities
            if not AgentClassEntity.is_online_at(entity, now)
        }

        online: list[_ScheduledProfile] = []
        offline: list[tuple[_ScheduledProfile, datetime]] = []
        profiles = self._scheduled_profiles(
            [entity.agent_class for entity in entities], self._settings.MAX_RUNS_PER_PROFILE_PER_MONTH
        )
        for profile in profiles:
            _, config = profile
            if config.agent_class in offline_last_seen:
                offline.append((profile, offline_last_seen[config.agent_class]))
            else:
                online.append(profile)

        window_start = self._clamp_window_start(watermark, now)
        return _SchedulableSnapshot(
            online=online,
            offline=offline,
            window_start=window_start,
            dropped_by_clamp=self._count_clamped_away(online, watermark, window_start),
            # Recomputed from live profiles rather than read from a marker on the thread, which is what
            # makes over-deletion unrepresentable: only a thread derived from a current profile can be
            # pruned. ThreadEntity carries no discriminator, and adding one would leave every already
            # created thread unlabelled with no migration mechanism in this repo to backfill it.
            scheduled_thread_ids=[
                str(ThreadEntity.scheduled_thread_id(AgentInstanceRef(agent_class=c.agent_class, agent_id=c.agent_id)))
                for _, c in online + [p for p, _ in offline]
            ],
        )

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
        return watermark if watermark >= earliest else earliest

    def _count_clamped_away(
        self,
        online: list[_ScheduledProfile],
        watermark: datetime,
        window_start: datetime,
    ) -> int:
        """Occurrences the clamp discarded, counted so a drop is reported rather than merely implied.

        The lag alone does not say whether any business work was actually lost.

        Capped, because this is the one span in a tick nothing else bounds: the firing window is clamped
        to `max_catchup`, but the *discarded* span is the whole outage, and the watermark key has no TTL.
        Left unbounded, a long enough outage — or a Redis restore carrying an old watermark — makes the
        count outrun the snapshot's timeout, and the tick then aborts before advancing the watermark, so
        the next tick faces a staler one still and the scheduler never fires again without manual repair.
        Liveness of the whole feature must not sit behind a number that only goes into a log line.

        Deliberately capped rather than moved after `set_watermark`: advancing the watermark before the
        occurrences in the window have been fired would trade this stall for lost runs.
        """
        if window_start <= watermark:
            return 0

        # Bounds the total rather than each profile, so the work is flat in profile count too. At roughly
        # 90k croniter steps a second this is a tenth of a second, against a tick budget of half the lease.
        budget = _MAX_CLAMPED_OCCURRENCES_COUNTED
        dropped = 0
        for schedule, _ in online:
            counted = CronScheduleCalculator.count_between(schedule, watermark, window_start, budget)
            dropped += counted
            budget -= counted
            if not budget:
                break

        logger.warning(
            "Scheduler was behind by %s; dropping %s occurrence(s) older than the %s catch-up window",
            window_start - watermark,
            f"at least {dropped}" if dropped == _MAX_CLAMPED_OCCURRENCES_COUNTED else dropped,
            self._max_catchup,
        )
        return dropped

    @staticmethod
    def _scheduled_profiles(
        agent_classes: list[str],
        max_runs_per_profile: int,
    ) -> list[tuple[CronSchedule, AgentConfigEntityDocument]]:
        """Profiles of the given classes that carry a parseable, admissible schedule.

        Paired with the schedule so the caller does not parse it twice.
        """
        instances: list[tuple[CronSchedule, AgentConfigEntityDocument]] = []
        for config in AgentConfigEntityDocument.find_for_classes(agent_classes):
            raw_schedule = (config.config_data or {}).get(CRON_CONFIG_KEY)
            # The same predicate the save path uses, rather than a falsy check restating it: an untouched
            # schedule group is stored as blank strings, which are truthy but not a schedule. Reading one
            # as malformed would put an ERROR with a traceback in the log on every tick, forever, for
            # every profile of a schedulable class that simply is not scheduled — burying the genuinely
            # broken rows this log exists to surface.
            if CronSchedule.is_unscheduled(raw_schedule):
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
            # The save path rejects an over-budget schedule, but only for rows written since it existed
            # and only while the setting held its current value. Lowering the ceiling must not leave the
            # profiles that were admissible under the old one firing forever, so the scan re-checks it —
            # the same write-time-validation-plus-scan-side-skip pairing a malformed schedule gets.
            runs = CronScheduleCalculator.runs_per_month(schedule, max_runs_per_profile + 1)
            if runs > max_runs_per_profile:
                logger.warning(
                    "Skipping %s/%s: its schedule runs more than %d times per 30 days, over this "
                    "deployment's per-agent limit. Edit the schedule, or raise "
                    "SCHEDULER_MAX_RUNS_PER_PROFILE_PER_MONTH.",
                    config.agent_class,
                    config.agent_id,
                    max_runs_per_profile,
                )
                continue
            instances.append((schedule, config))
        return instances

    @staticmethod
    def _report_occurrences_dropped_while_offline(
        snapshot: _SchedulableSnapshot,
        window_start: datetime,
        now: datetime,
        report: _TickReport,
    ) -> None:
        """Reports the occurrences this tick passed over because the blueprint had no runner online.

        Dropping them is the intended behaviour — the scheduler does not queue work for an agent that
        cannot consume it, and a run whose moment has passed is rarely worth firing late. But the
        watermark advances either way, so they are gone rather than deferred, and silence made that
        indistinguishable from a schedule that simply had nothing due.

        Pure: the profiles and their last-seen times come from the tick's snapshot, so reporting a drop
        costs no extra query.
        """
        for (schedule, config), last_seen in snapshot.offline:
            dropped = CronScheduleCalculator.occurrences_between(schedule, window_start, now)
            if not dropped:
                continue
            report.dropped_offline += len(dropped)
            logger.warning(
                "Skipped %d occurrence(s) for %s/%s — class offline since %s",
                len(dropped),
                config.agent_class,
                config.agent_id,
                last_seen,
            )

    async def _fire_occurrences(
        self,
        schedule: CronSchedule,
        config: AgentConfigEntityDocument,
        window_start: datetime,
        now: datetime,
        report: _TickReport,
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
            # Deliberately not fail-fast, for the same reason a malformed schedule is skipped rather
            # than raised: the loop over profiles is shared. Letting a publish failure propagate aborts
            # the window before the watermark advances, so every *other* profile loses its due
            # occurrences too and the next tick rediscovers the same broken row. The occurrence stays
            # claimed, keeping the at-most-once posture the no-duplicate-runs guarantee is built on.
            try:
                await self._start_run(config, occurrence)
            except Exception:
                report.publish_failures += 1
                self._report_publish_failure(config, occurrence, report)
            else:
                report.occurrences_fired += 1

    @staticmethod
    def _report_publish_failure(
        config: AgentConfigEntityDocument,
        occurrence: datetime,
        report: _TickReport,
    ) -> None:
        """Reports one lost run, with the stack attached only to the first failure of the tick.

        Every failure gets a line, because each one is a distinct business run that did not happen — the
        watermark advances either way, so nothing will retry it. But when the cause is systemic (a broker
        outage takes down every profile at once) the stacks are identical, and repeating one per
        occurrence buries the profile names that are the useful part. So the first failure carries the
        traceback and the rest carry the identity, with `publish_failures` in the tick summary giving the
        total.

        Volume is bounded by schedule density rather than by tick rate: an occurrence is attempted once
        and logged once, because the watermark advances past it whether the publish succeeded or not.
        """
        detail = (
            "Failed to start scheduled run for %s/%s (occurrence %s); the occurrence stays claimed and "
            "will not be retried"
        )
        if report.publish_failures == 1:
            logger.exception(detail, config.agent_class, config.agent_id, occurrence.isoformat())
            return

        logger.error(
            f"{detail} (failure %d this tick; see the first for the traceback)",
            config.agent_class,
            config.agent_id,
            occurrence.isoformat(),
            report.publish_failures,
        )

    async def _start_run(self, config: AgentConfigEntityDocument, occurrence: datetime) -> None:
        """Publishes a scheduled start event on the normal agent control path."""
        agent = AgentInstanceRef(agent_class=config.agent_class, agent_id=config.agent_id)
        # Query plus conditional insert, and it runs once per fired occurrence rather than once per tick.
        thread = await asyncio.to_thread(ThreadEntity.get_or_create_scheduled_thread, _SCHEDULED_THREAD_NAME, agent)

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

    async def _prune_scheduled_history(
        self,
        snapshot: _SchedulableSnapshot,
        now: datetime,
        report: _TickReport,
        elapsed_seconds: float,
    ) -> None:
        """Bounds how much run history one scheduled thread accumulates.

        Every scheduled run of a profile shares one thread, so nothing bounds that thread's event count —
        a `*/5` schedule eventually makes it expensive to open. Only the events are pruned: the thread id
        is derived from the profile, so deleting the document merely makes the next fire recreate it.

        Runs inside the leader lease already held by the tick, which is free — a separate loop would
        contend for the same key and starve one of the two — but gated to at most once per retention
        interval cluster-wide, because a bulk delete has no business on the per-tick path.
        """
        retention = self._settings.event_retention
        if retention is None or not snapshot.scheduled_thread_ids:
            return
        if not await self._store.claim_retention_window(self._settings.RETENTION_INTERVAL_SECONDS):
            return

        started = time.monotonic()
        # Bounded by what is *left* of the lease, not by the whole of it. The snapshot read may already
        # have spent up to half, so a flat `lease_ttl` here would let one tick run to 1.5x the lease and
        # break the invariant the lease exists to hold.
        remaining_lease = max(1.0, self._lease_ttl - elapsed_seconds)
        try:
            report.events_pruned = await asyncio.wait_for(
                asyncio.to_thread(
                    PersistedAgentEventEntity.delete_events_older_than,
                    snapshot.scheduled_thread_ids,
                    now - retention,
                ),
                timeout=remaining_lease,
            )
        except TimeoutError:
            # Never fail the tick over retention: the runs are what matter, and the next interval retries.
            logger.warning(
                "Pruning scheduled-run history exceeded the %.0fs left of the lease and was abandoned; "
                "it will be retried next interval",
                remaining_lease,
            )
            return

        if report.events_pruned:
            logger.info(
                "Pruned %d scheduled-run event(s) older than %s across %d thread(s) in %.1fs",
                report.events_pruned,
                now - retention,
                len(snapshot.scheduled_thread_ids),
                time.monotonic() - started,
            )

    @staticmethod
    def _log_tick_summary(report: _TickReport, duration_seconds: float) -> None:
        """One fixed-cardinality line per tick, so a drop or a failure can be alerted on.

        Quiet when a tick did nothing interesting, which is most of them — a scheduler with no due work
        should not fill the log.
        """
        if not any(
            (
                report.occurrences_fired,
                report.dropped_by_clamp,
                report.dropped_offline,
                report.publish_failures,
                report.events_pruned,
            )
        ):
            return

        logger.info(
            "Scheduler tick: profiles_scanned=%d occurrences_fired=%d dropped_by_clamp=%d "
            "dropped_offline=%d publish_failures=%d events_pruned=%d duration_ms=%d",
            report.profiles_scanned,
            report.occurrences_fired,
            report.dropped_by_clamp,
            report.dropped_offline,
            report.publish_failures,
            report.events_pruned,
            int(duration_seconds * 1000),
        )
