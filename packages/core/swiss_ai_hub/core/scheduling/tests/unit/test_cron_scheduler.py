import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from swiss_ai_hub.core.events.agent.control.start.cron_start_event import CronStartEvent
from swiss_ai_hub.core.scheduling.cron_scheduler import CronScheduler

_MODULE = "swiss_ai_hub.core.scheduling.cron_scheduler"
_NOW = datetime(2026, 8, 11, 12, 0, 30, tzinfo=UTC)
_HOURLY = {"minute": "0", "hour": "*", "day_of_month": "*", "month": "*", "day_of_week": "*", "timezone": "UTC"}


def _config(agent_class: str = "CronDemoAgent", agent_id: str = "demo", schedule: dict | None = _HOURLY):
    return SimpleNamespace(
        agent_class=agent_class,
        agent_id=agent_id,
        config_data={"cron": schedule} if schedule else {},
    )


def _agent_class(
    agent_class: str = "CronDemoAgent",
    last_discovered: datetime = _NOW - timedelta(hours=2),
):
    return SimpleNamespace(agent_class=agent_class, last_discovered=last_discovered)


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
    offline_classes: list | None = None,
) -> MagicMock:
    """Runs one tick with everything it reaches out to patched, returning the thread-resolution mock.

    Only the scheduling logic is left real — leadership, persistence, and the distributor are all fakes.
    """
    service._store.leadership = lambda: _leadership(is_leader)
    service._store.get_watermark = AsyncMock(return_value=watermark)
    service._store.set_watermark = AsyncMock()
    service._store.claim_occurrence = AsyncMock(return_value=claimed)

    online_classes = (agent_classes if agent_classes is not None else [_agent_class()]) if schedulable else []
    with (
        patch(f"{_MODULE}.datetime", **{"now.return_value": _NOW}),
        patch(f"{_MODULE}.AgentClassEntity.get_online_schedulable", return_value=online_classes),
        patch(f"{_MODULE}.AgentClassEntity.get_offline_schedulable", return_value=offline_classes or []),
        patch(f"{_MODULE}.AgentConfigEntityDocument.find_for_classes", return_value=configs or [_config()]),
        patch(f"{_MODULE}.ThreadEntity.get_or_create_scheduled_thread") as scheduled_thread,
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
        offline_since = _NOW - timedelta(hours=2)
        with caplog.at_level(logging.WARNING):
            await _run_tick(
                service,
                schedulable=False,
                offline_classes=[_agent_class(last_discovered=offline_since)],
            )

        assert "Skipped 1 occurrence(s) for CronDemoAgent/demo" in caplog.text
        assert str(offline_since) in caplog.text

    @pytest.mark.asyncio
    async def test_still_fires_nothing_for_an_offline_class(
        self, service: CronScheduler, distributor: MagicMock
    ) -> None:
        """The warning reports the drop; it must not become a late run."""
        await _run_tick(service, schedulable=False, offline_classes=[_agent_class()])

        distributor.distribute_event.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_stays_quiet_when_an_offline_class_had_nothing_due(
        self, service: CronScheduler, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Offline is not itself the problem — only losing a run to it is."""
        with caplog.at_level(logging.WARNING):
            await _run_tick(
                service,
                schedulable=False,
                offline_classes=[_agent_class()],
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
                schedulable=False,
                offline_classes=[_agent_class()],
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

        assert service._clamp_window_start(stale, _NOW) == _NOW - timedelta(minutes=15)

    def test_keeps_a_recent_watermark(self, service: CronScheduler) -> None:
        recent = _NOW - timedelta(minutes=1)

        assert service._clamp_window_start(recent, _NOW) == recent
