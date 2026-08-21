import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from swiss_ai_hub.core.events.agent.control.start.cron_start_event import CronStartEvent
from swiss_ai_hub.core.scheduling.cron_schedule import CronSchedule
from swiss_ai_hub.core.scheduling.cron_scheduler import CronScheduler, _SchedulableSnapshot, _TickReport
from swiss_ai_hub.core.scheduling.scheduler_settings import SchedulerSettings

_MODULE = "swiss_ai_hub.core.scheduling.cron_scheduler"
_NOW = datetime(2026, 8, 11, 12, 0, 30, tzinfo=UTC)
_HOURLY = {"minute": "0", "hour": "*", "day_of_month": "*", "month": "*", "day_of_week": "*", "timezone": "UTC"}
_EVERY_FIVE_MINUTES = {**_HOURLY, "minute": "*/5"}
# AgentClassEntity.last_discovered is stored naive, and the online/offline split compares against it.
_NAIVE_NOW = _NOW.replace(tzinfo=None)


def _config(agent_class: str = "CronDemoAgent", agent_id: str = "demo", schedule: dict | None = _HOURLY):
    return SimpleNamespace(
        agent_class=agent_class,
        agent_id=agent_id,
        config_data={"cron": schedule} if schedule else {},
    )


def _agent_class(agent_class: str = "CronDemoAgent", last_discovered: datetime | None = None):
    """A discovered class, online by default. Pass an older `last_discovered` to make it offline."""
    return SimpleNamespace(
        agent_class=agent_class,
        last_discovered=_NAIVE_NOW if last_discovered is None else last_discovered,
    )


def _snapshot_hops(to_thread: MagicMock) -> int:
    """How many of the offloaded calls were the snapshot read. Mocked callables carry no `__name__`."""
    return sum(
        getattr(call.args[0], "__name__", "") == "_load_schedulable_snapshot" for call in to_thread.call_args_list
    )


def _snapshot(online: list | None = None) -> _SchedulableSnapshot:
    return _SchedulableSnapshot(online=online or [])


def _offline_agent_class(agent_class: str = "CronDemoAgent"):
    return _agent_class(agent_class, last_discovered=_NAIVE_NOW - timedelta(hours=2))


@pytest.fixture
def distributor() -> MagicMock:
    distributor = MagicMock()
    distributor.distribute_event = AsyncMock()
    return distributor


@pytest.fixture
def service(distributor: MagicMock) -> CronScheduler:
    return CronScheduler(redis=MagicMock(), external_agent_event_distributor=distributor)


@asynccontextmanager
async def _leadership(is_leader: bool):
    yield is_leader


async def _run_tick(
    service: CronScheduler,
    *,
    is_leader: bool = True,
    watermark: datetime | None = datetime(2026, 8, 11, 11, 30, tzinfo=UTC),
    claimed: bool = True,
    configs: list | None = None,
    schedulable: bool = True,
    agent_classes: list | None = None,
    claim_retention: bool = False,
) -> MagicMock:
    """Runs one tick with everything it reaches out to patched, returning the thread-resolution mock.

    Only the persistence reads, leadership, and the distributor are faked; the online/offline split and
    the schedule parsing inside the snapshot stay real, since that is where the tick's decisions are made.
    """
    service._store.leadership = lambda: _leadership(is_leader)
    service._store.get_watermark = AsyncMock(return_value=watermark)
    service._store.set_watermark = AsyncMock()
    service._store.claim_occurrence = AsyncMock(return_value=claimed)
    service._store.claim_retention_window = AsyncMock(return_value=claim_retention)

    classes = (agent_classes if agent_classes is not None else [_agent_class()]) if schedulable else []
    with (
        patch(f"{_MODULE}.datetime", **{"now.return_value": _NOW}),
        patch(f"{_MODULE}.AgentClassEntity.get_all_schedulable", return_value=classes),
        patch(f"{_MODULE}.AgentConfigEntityDocument.find_for_classes", return_value=configs or [_config()]),
        patch(f"{_MODULE}.ThreadEntity.get_or_create_scheduled_thread") as scheduled_thread,
        patch(f"{_MODULE}.ThreadEntity.scheduled_thread_id", return_value="thread-1"),
    ):
        scheduled_thread.return_value = SimpleNamespace(id="thread-1")
        await service._tick()
        return scheduled_thread


class TestLeadership:
    @pytest.mark.asyncio
    async def test_non_leader_fires_nothing(self, service: CronScheduler, distributor: MagicMock) -> None:
        await _run_tick(service, is_leader=False)

        distributor.distribute_event.assert_not_awaited()
        service._store.set_watermark.assert_not_awaited()


class TestColdStart:
    @pytest.mark.asyncio
    async def test_adopts_the_current_time_without_firing(self, service: CronScheduler, distributor: MagicMock) -> None:
        """Without this, the first tick would replay every occurrence a schedule ever had."""
        await _run_tick(service, watermark=None)

        distributor.distribute_event.assert_not_awaited()
        service._store.set_watermark.assert_awaited_once_with(_NOW)


class TestFiring:
    @pytest.mark.asyncio
    async def test_fires_the_due_occurrence(self, service: CronScheduler, distributor: MagicMock) -> None:
        await _run_tick(service)

        distributor.distribute_event.assert_awaited_once()
        external_event = distributor.distribute_event.call_args[0][0]
        assert isinstance(external_event.event, CronStartEvent)
        assert external_event.event.scheduled_for == datetime(2026, 8, 11, 12, tzinfo=UTC)

    @pytest.mark.asyncio
    async def test_fires_as_a_system_run_without_a_user(self, service: CronScheduler, distributor: MagicMock) -> None:
        """A user on the run would let it be mistaken for user-initiated and would imply an
        execution identity that scheduled runs deliberately do not have."""
        await _run_tick(service)

        assert distributor.distribute_event.call_args.kwargs["user"] is None
        assert distributor.distribute_event.call_args[0][0].event.user is None

    @pytest.mark.asyncio
    async def test_targets_the_scheduled_agent(self, service: CronScheduler, distributor: MagicMock) -> None:
        await _run_tick(service)

        target = distributor.distribute_event.call_args.kwargs["target_agent"]
        assert (target.agent_class, target.agent_id) == ("CronDemoAgent", "demo")

    @pytest.mark.asyncio
    async def test_fires_into_the_profile_thread(self, service: CronScheduler) -> None:
        """One thread per profile, not per occurrence: a five-minute schedule would otherwise leave
        ~105k single-run threads a year with nothing to clean them up. Membership is #1582's concern;
        the thread this resolves to still has none."""
        scheduled_thread = await _run_tick(service)

        agent = scheduled_thread.call_args[0][1]
        assert (agent.agent_class, agent.agent_id) == ("CronDemoAgent", "demo")

    @pytest.mark.asyncio
    async def test_advances_the_watermark(self, service: CronScheduler) -> None:
        await _run_tick(service)

        service._store.set_watermark.assert_awaited_once_with(_NOW)


class TestExactlyOnce:
    @pytest.mark.asyncio
    async def test_skips_an_occurrence_another_replica_claimed(
        self, service: CronScheduler, distributor: MagicMock
    ) -> None:
        await _run_tick(service, claimed=False)

        distributor.distribute_event.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_claims_before_firing(self, service: CronScheduler) -> None:
        await _run_tick(service)

        service._store.claim_occurrence.assert_awaited_once_with(
            "CronDemoAgent", "demo", datetime(2026, 8, 11, 12, tzinfo=UTC)
        )


class TestPublishFailureIsolation:
    """A publish that raises used to propagate out of the whole tick, taking every other profile with it."""

    @pytest.mark.asyncio
    async def test_a_failing_publish_does_not_starve_the_other_profiles(
        self, service: CronScheduler, distributor: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Same rationale as a malformed schedule: the loop over profiles is shared, so an uncaught failure
        aborts the window before the watermark advances and every later tick rediscovers the same row."""

        async def fail_only_for_broken(_event, *, user, target_agent):
            if target_agent.agent_id == "broken":
                raise RuntimeError("NATS unavailable")

        distributor.distribute_event.side_effect = fail_only_for_broken

        with caplog.at_level(logging.ERROR):
            await _run_tick(service, configs=[_config(agent_id="broken"), _config(agent_id="healthy")])

        attempted = {call.kwargs["target_agent"].agent_id for call in distributor.distribute_event.call_args_list}
        assert attempted == {"broken", "healthy"}
        assert "Failed to start scheduled run for CronDemoAgent/broken" in caplog.text

    @pytest.mark.asyncio
    async def test_a_failing_publish_still_advances_the_watermark(
        self, service: CronScheduler, distributor: MagicMock
    ) -> None:
        """Leaving the watermark behind would replay the whole window on the next tick."""
        distributor.distribute_event.side_effect = RuntimeError("NATS unavailable")

        await _run_tick(service, configs=[_config(agent_id="broken")])

        service._store.set_watermark.assert_awaited_once_with(_NOW)

    @pytest.mark.asyncio
    async def test_a_failure_does_not_stop_later_occurrences_of_the_same_profile(
        self, service: CronScheduler, distributor: MagicMock
    ) -> None:
        """The guard sits inside the per-occurrence loop, not around it.

        Profile-level isolation comes from the caller's loop, so it survives the guard being hoisted to
        wrap this whole method — which is exactly the "simplification" someone would reach for. Only a
        profile with several due occurrences pins where the guard actually belongs.
        """
        distributor.distribute_event.side_effect = [RuntimeError("NATS unavailable"), None, None]

        # A */5 schedule over the clamped 15-minute catch-up window: three occurrences, one profile.
        await _run_tick(service, configs=[_config(schedule=_EVERY_FIVE_MINUTES)])

        assert distributor.distribute_event.await_count == 3

    @pytest.mark.asyncio
    async def test_a_failed_occurrence_is_not_released(self, service: CronScheduler, distributor: MagicMock) -> None:
        """At-most-once is the right way round given the no-duplicate-runs guarantee, so a failed
        occurrence must not be handed back.

        There is no release path today, and this pins that there isn't one: the tempting fix for a
        transient publish failure is to release the claim so the next tick retries it, which would turn a
        dropped run into a duplicated one. The claim is a Redis key, so releasing it means deleting it.
        """
        distributor.distribute_event.side_effect = RuntimeError("NATS unavailable")

        await _run_tick(service, configs=[_config(agent_id="broken")])

        removals = [call for call in service._store._redis.mock_calls if "delete" in call[0] or "unlink" in call[0]]
        assert removals == []


class TestInstanceSelection:
    @pytest.mark.asyncio
    async def test_ignores_instances_without_a_schedule(self, service: CronScheduler, distributor: MagicMock) -> None:
        """A schedulable blueprint does not oblige every profile of it to be scheduled."""
        await _run_tick(service, configs=[_config(schedule=None)])

        distributor.distribute_event.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_fires_each_scheduled_instance(self, service: CronScheduler, distributor: MagicMock) -> None:
        await _run_tick(service, configs=[_config(agent_id="a"), _config(agent_id="b"), _config(schedule=None)])

        fired = {call.kwargs["target_agent"].agent_id for call in distributor.distribute_event.call_args_list}
        assert fired == {"a", "b"}

    @pytest.mark.asyncio
    async def test_one_malformed_schedule_does_not_starve_the_others(
        self, service: CronScheduler, distributor: MagicMock
    ) -> None:
        """The config save path validates against a generated schema that cannot carry CronSchedule's
        validators, so a malformed schedule can reach storage. Letting it raise would abort the tick
        before the watermark advanced and every later tick would rediscover the same row — one bad
        profile would permanently stop every other schedule."""
        malformed = _config(
            agent_id="broken",
            schedule={
                "minute": "99",
                "hour": "*",
                "day_of_month": "*",
                "month": "*",
                "day_of_week": "*",
                "timezone": "UTC",
            },
        )
        await _run_tick(service, configs=[malformed, _config(agent_id="healthy")])

        fired = {call.kwargs["target_agent"].agent_id for call in distributor.distribute_event.call_args_list}
        assert fired == {"healthy"}

    @pytest.mark.asyncio
    async def test_a_malformed_schedule_still_advances_the_watermark(self, service: CronScheduler) -> None:
        await _run_tick(service, configs=[_config(agent_id="broken", schedule={"minute": "99"})])

        service._store.set_watermark.assert_awaited_once_with(_NOW)

    @pytest.mark.asyncio
    async def test_does_nothing_when_no_class_is_schedulable(
        self, service: CronScheduler, distributor: MagicMock
    ) -> None:
        """An offline or non-schedulable class must not fire, even if a profile still carries a schedule."""
        await _run_tick(service, schedulable=False)

        distributor.distribute_event.assert_not_awaited()


class TestDiagnostics:
    """These only log. The behaviour they describe is deliberate, so the tests assert that it is
    still in force — a warning that had quietly become a behaviour change would be worse than none."""

    @pytest.mark.asyncio
    async def test_warns_when_the_watermark_sits_in_the_future(
        self, service: CronScheduler, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A fast-clocked replica writes a watermark ahead of real time and every replica then fires
        nothing, with no error to show for it. The warning is the only signal that this is happening."""
        with caplog.at_level(logging.WARNING):
            await _run_tick(service, watermark=_NOW + timedelta(hours=1))

        assert "ahead of this replica's clock" in caplog.text

    @pytest.mark.asyncio
    async def test_a_future_watermark_is_still_allowed_to_be_overwritten(self, service: CronScheduler) -> None:
        """The watermark must stay free to move backwards — that is what lets a correctly-clocked
        replica repair a skewed one. Making it monotonic would freeze the skew in place permanently."""
        await _run_tick(service, watermark=_NOW + timedelta(hours=1))

        service._store.set_watermark.assert_awaited_once_with(_NOW)

    @pytest.mark.asyncio
    async def test_stays_quiet_on_a_normal_tick(self, service: CronScheduler, caplog: pytest.LogCaptureFixture) -> None:
        """A watermark inside the catch-up window and a clock that agrees with it — no diagnostics."""
        with caplog.at_level(logging.WARNING):
            await _run_tick(service, watermark=_NOW - timedelta(minutes=5))

        assert caplog.text == ""

    def test_warns_when_a_tick_outruns_its_lease(
        self, service: CronScheduler, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.WARNING):
            service._warn_if_tick_outran_its_lease(service._lease_ttl + 1)

        assert "outrunning its" in caplog.text

    def test_silent_when_a_tick_finishes_inside_its_lease(
        self, service: CronScheduler, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.WARNING):
            service._warn_if_tick_outran_its_lease(0.01)

        assert caplog.text == ""


class TestOccurrencesDroppedWhileOffline:
    """An occurrence falling due with no runner online is dropped, not queued — the watermark advances
    either way. That is deliberate, and it used to be indistinguishable from having nothing due."""

    @pytest.mark.asyncio
    async def test_warns_about_what_was_dropped(self, service: CronScheduler, caplog: pytest.LogCaptureFixture) -> None:
        offline_since = _NAIVE_NOW - timedelta(hours=2)
        with caplog.at_level(logging.WARNING):
            await _run_tick(
                service,
                agent_classes=[_agent_class(last_discovered=offline_since)],
            )

        assert "Skipped 1 occurrence(s) for CronDemoAgent/demo" in caplog.text
        assert str(offline_since) in caplog.text

    @pytest.mark.asyncio
    async def test_still_fires_nothing_for_an_offline_class(
        self, service: CronScheduler, distributor: MagicMock
    ) -> None:
        """The warning reports the drop; it must not become a late run."""
        await _run_tick(service, agent_classes=[_offline_agent_class()])

        distributor.distribute_event.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_stays_quiet_when_an_offline_class_had_nothing_due(
        self, service: CronScheduler, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Offline is not itself the problem — only losing a run to it is."""
        with caplog.at_level(logging.WARNING):
            await _run_tick(
                service,
                agent_classes=[_offline_agent_class()],
                watermark=_NOW - timedelta(seconds=5),
            )

        assert caplog.text == ""

    @pytest.mark.asyncio
    async def test_stays_quiet_when_an_offline_profile_has_no_schedule(
        self, service: CronScheduler, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.WARNING):
            await _run_tick(
                service,
                agent_classes=[_offline_agent_class()],
                configs=[_config(schedule=None)],
                watermark=_NOW - timedelta(minutes=5),
            )

        assert caplog.text == ""


class TestCatchUp:
    @pytest.mark.asyncio
    async def test_replays_occurrences_inside_the_catch_up_window(
        self, service: CronScheduler, distributor: MagicMock
    ) -> None:
        await _run_tick(service, watermark=_NOW - timedelta(minutes=10))

        distributor.distribute_event.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_drops_occurrences_older_than_the_catch_up_window(
        self, service: CronScheduler, distributor: MagicMock
    ) -> None:
        """After long downtime a stale watermark would otherwise produce a burst of runs whose
        scheduled moment has long passed."""
        await _run_tick(service, watermark=_NOW - timedelta(days=3))

        assert distributor.distribute_event.await_count == 1

    def test_clamps_the_window_start_to_the_catch_up_horizon(self, service: CronScheduler) -> None:
        stale = _NOW - timedelta(days=3)

        assert service._clamp_window_start(stale, _NOW, _snapshot(), _TickReport()) == _NOW - timedelta(minutes=15)

    def test_keeps_a_recent_watermark(self, service: CronScheduler) -> None:
        recent = _NOW - timedelta(minutes=1)

        assert service._clamp_window_start(recent, _NOW, _snapshot(), _TickReport()) == recent

    def test_counts_the_occurrences_the_clamp_discarded(self, service: CronScheduler) -> None:
        """The lag alone does not say whether any business work was actually lost."""
        report = _TickReport()
        schedule = CronSchedule.model_validate(_HOURLY)

        service._clamp_window_start(_NOW - timedelta(days=1), _NOW, _snapshot([(schedule, _config())]), report)

        assert report.dropped_by_clamp == 23


class TestTheTickStaysOffTheEventLoop:
    """The scheduler runs inside the API process, so a synchronous Mongo read in the tick stalls every
    HTTP and WebSocket request for its duration — and the stall grows with the profile count."""

    @pytest.mark.asyncio
    async def test_the_snapshot_read_is_offloaded_to_a_thread(self, service: CronScheduler) -> None:
        with patch(f"{_MODULE}.asyncio.to_thread", wraps=asyncio.to_thread) as to_thread:
            await _run_tick(service)

        assert _snapshot_hops(to_thread) == 1

    @pytest.mark.asyncio
    async def test_resolving_the_thread_is_offloaded_too(self, service: CronScheduler) -> None:
        """A query plus conditional insert, and it runs once per fired occurrence rather than per tick."""
        with patch(f"{_MODULE}.asyncio.to_thread", wraps=asyncio.to_thread) as to_thread:
            scheduled_thread = await _run_tick(service)

        assert any(call.args[0] is scheduled_thread for call in to_thread.call_args_list)

    @pytest.mark.asyncio
    async def test_the_whole_snapshot_is_one_hop_regardless_of_profile_count(self, service: CronScheduler) -> None:
        """Reading classes and profiles separately would cost a hop each, every tick."""
        with patch(f"{_MODULE}.asyncio.to_thread", wraps=asyncio.to_thread) as to_thread:
            await _run_tick(service, configs=[_config(agent_id="a"), _config(agent_id="b")])

        assert _snapshot_hops(to_thread) == 1


class TestRetention:
    """Every scheduled run of a profile shares one thread, so nothing bounds that thread's history."""

    @pytest.mark.asyncio
    async def test_pruning_is_disabled_by_default(self, service: CronScheduler) -> None:
        """Merging this code must not start deleting anyone's history — an operator has to ask for it."""
        with patch(f"{_MODULE}.PersistedAgentEventEntity.delete_events_older_than") as prune:
            await _run_tick(service)

        prune.assert_not_called()

    @pytest.mark.asyncio
    async def test_prunes_events_older_than_the_retention_window(self, distributor: MagicMock) -> None:
        service = CronScheduler(
            redis=MagicMock(),
            external_agent_event_distributor=distributor,
            settings=SchedulerSettings(EVENT_RETENTION_DAYS=7),
        )
        with patch(f"{_MODULE}.PersistedAgentEventEntity.delete_events_older_than", return_value=3) as prune:
            service._store.claim_retention_window = AsyncMock(return_value=True)
            await _run_tick(service, claim_retention=True)

        assert prune.call_args.args[0] == ["thread-1"]
        assert prune.call_args.args[1] == _NOW - timedelta(days=7)

    @pytest.mark.asyncio
    async def test_another_replica_holding_the_window_skips_the_prune(self, distributor: MagicMock) -> None:
        """The claim is what keeps a bulk delete off the per-tick path."""
        service = CronScheduler(
            redis=MagicMock(),
            external_agent_event_distributor=distributor,
            settings=SchedulerSettings(EVENT_RETENTION_DAYS=7),
        )
        with patch(f"{_MODULE}.PersistedAgentEventEntity.delete_events_older_than") as prune:
            await _run_tick(service)

        prune.assert_not_called()

    @pytest.mark.asyncio
    async def test_a_slow_prune_does_not_fail_the_tick(self, distributor: MagicMock) -> None:
        """Retention is housekeeping; the runs are what matter. The next interval retries."""
        service = CronScheduler(
            redis=MagicMock(),
            external_agent_event_distributor=distributor,
            settings=SchedulerSettings(EVENT_RETENTION_DAYS=7),
        )
        with patch(f"{_MODULE}.asyncio.wait_for", side_effect=[_SchedulableSnapshot(), TimeoutError()]):
            await _run_tick(service, claim_retention=True)

        service._store.set_watermark.assert_awaited_once()


class TestPublishFailureReporting:
    """Under a systemic outage every scheduled profile fails at once with the same stack."""

    @pytest.mark.asyncio
    async def test_a_failure_does_not_stop_later_occurrences_of_the_same_profile(
        self, service: CronScheduler, distributor: MagicMock
    ) -> None:
        """The guard sits inside the per-occurrence loop, not around it. Profile isolation comes from the
        caller's loop and would survive hoisting the guard, so only a multi-occurrence profile pins it."""
        distributor.distribute_event.side_effect = [RuntimeError("NATS unavailable"), None, None]

        await _run_tick(service, configs=[_config(schedule=_EVERY_FIVE_MINUTES)])

        assert distributor.distribute_event.await_count == 3

    @pytest.mark.asyncio
    async def test_every_lost_run_is_named(
        self, service: CronScheduler, distributor: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Collapsing these would hide which profiles lost work, which is the useful part."""
        distributor.distribute_event.side_effect = RuntimeError("NATS unavailable")

        with caplog.at_level(logging.ERROR):
            await _run_tick(service, configs=[_config(agent_id="a"), _config(agent_id="b")])

        assert "CronDemoAgent/a" in caplog.text
        assert "CronDemoAgent/b" in caplog.text

    @pytest.mark.asyncio
    async def test_only_the_first_failure_of_a_tick_carries_a_traceback(
        self, service: CronScheduler, distributor: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A broker outage makes every stack identical, so repeating them buries the identities."""
        distributor.distribute_event.side_effect = RuntimeError("NATS unavailable")

        with caplog.at_level(logging.ERROR):
            await _run_tick(service, configs=[_config(agent_id="a"), _config(agent_id="b"), _config(agent_id="c")])

        assert len([record for record in caplog.records if record.exc_info]) == 1
        assert caplog.text.count("Failed to start scheduled run") == 3

    @pytest.mark.asyncio
    async def test_the_tick_summary_carries_the_total(
        self, service: CronScheduler, distributor: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        distributor.distribute_event.side_effect = RuntimeError("NATS unavailable")

        with caplog.at_level(logging.INFO):
            await _run_tick(service, configs=[_config(agent_id="a"), _config(agent_id="b")])

        assert "publish_failures=2" in caplog.text
