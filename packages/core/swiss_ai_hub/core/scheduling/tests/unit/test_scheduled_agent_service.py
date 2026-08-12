from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from swiss_ai_hub.core.events.agent.control.start.scheduled_start_event import ScheduledStartEvent
from swiss_ai_hub.core.scheduling.scheduled_agent_service import ScheduledAgentService

_MODULE = "swiss_ai_hub.core.scheduling.scheduled_agent_service"
_NOW = datetime(2026, 8, 11, 12, 0, 30, tzinfo=UTC)
_HOURLY = {"minute": "0", "hour": "*", "day_of_month": "*", "month": "*", "day_of_week": "*", "timezone": "UTC"}


def _config(agent_class: str = "ScheduledDemoAgent", agent_id: str = "demo", schedule: dict | None = _HOURLY):
    return SimpleNamespace(
        agent_class=agent_class,
        agent_id=agent_id,
        config_data={"schedule": schedule} if schedule else {},
    )


@pytest.fixture
def distributor() -> MagicMock:
    distributor = MagicMock()
    distributor.distribute_event = AsyncMock()
    return distributor


@pytest.fixture
def service(distributor: MagicMock) -> ScheduledAgentService:
    return ScheduledAgentService(redis=MagicMock(), external_agent_event_distributor=distributor)


@asynccontextmanager
async def _leadership(is_leader: bool):
    yield is_leader


async def _run_tick(
    service: ScheduledAgentService,
    *,
    is_leader: bool = True,
    watermark: datetime | None = datetime(2026, 8, 11, 11, 30, tzinfo=UTC),
    claimed: bool = True,
    configs: list | None = None,
    schedulable: bool = True,
) -> MagicMock:
    """Runs one tick with everything it reaches out to patched, returning the thread-creation mock.

    Only the scheduling logic is left real — leadership, persistence, and the distributor are all fakes.
    """
    service._store.leadership = lambda: _leadership(is_leader)
    service._store.get_watermark = AsyncMock(return_value=watermark)
    service._store.set_watermark = AsyncMock()
    service._store.claim_occurrence = AsyncMock(return_value=claimed)

    online_classes = [SimpleNamespace(agent_class="ScheduledDemoAgent")] if schedulable else []
    with (
        patch(f"{_MODULE}.datetime", **{"now.return_value": _NOW}),
        patch(f"{_MODULE}.AgentClassEntity.get_online_schedulable", return_value=online_classes),
        patch(f"{_MODULE}.AgentConfigEntityDocument.find_for_classes", return_value=configs or [_config()]),
        patch(f"{_MODULE}.ThreadEntity.create_thread") as create_thread,
    ):
        create_thread.return_value = SimpleNamespace(id="thread-1")
        await service._tick()
        return create_thread


class TestLeadership:
    @pytest.mark.asyncio
    async def test_non_leader_fires_nothing(self, service: ScheduledAgentService, distributor: MagicMock) -> None:
        await _run_tick(service, is_leader=False)

        distributor.distribute_event.assert_not_awaited()
        service._store.set_watermark.assert_not_awaited()


class TestColdStart:
    @pytest.mark.asyncio
    async def test_adopts_the_current_time_without_firing(
        self, service: ScheduledAgentService, distributor: MagicMock
    ) -> None:
        """Without this, the first tick would replay every occurrence a schedule ever had."""
        await _run_tick(service, watermark=None)

        distributor.distribute_event.assert_not_awaited()
        service._store.set_watermark.assert_awaited_once_with(_NOW)


class TestFiring:
    @pytest.mark.asyncio
    async def test_fires_the_due_occurrence(self, service: ScheduledAgentService, distributor: MagicMock) -> None:
        await _run_tick(service)

        distributor.distribute_event.assert_awaited_once()
        external_event = distributor.distribute_event.call_args[0][0]
        assert isinstance(external_event.event, ScheduledStartEvent)
        assert external_event.event.scheduled_for == datetime(2026, 8, 11, 12, tzinfo=UTC)

    @pytest.mark.asyncio
    async def test_fires_as_a_system_run_without_a_user(
        self, service: ScheduledAgentService, distributor: MagicMock
    ) -> None:
        """A user on the run would let it be mistaken for user-initiated and would imply an
        execution identity that scheduled runs deliberately do not have."""
        await _run_tick(service)

        assert distributor.distribute_event.call_args.kwargs["user"] is None
        assert distributor.distribute_event.call_args[0][0].event.user is None

    @pytest.mark.asyncio
    async def test_targets_the_scheduled_agent(self, service: ScheduledAgentService, distributor: MagicMock) -> None:
        await _run_tick(service)

        target = distributor.distribute_event.call_args.kwargs["target_agent"]
        assert (target.agent_class, target.agent_id) == ("ScheduledDemoAgent", "demo")

    @pytest.mark.asyncio
    async def test_creates_a_thread_with_no_members(self, service: ScheduledAgentService) -> None:
        """v1 fires into a system thread; configurable membership is a separate concern."""
        create_thread = await _run_tick(service)

        assert create_thread.call_args.kwargs["users"] == []

    @pytest.mark.asyncio
    async def test_advances_the_watermark(self, service: ScheduledAgentService) -> None:
        await _run_tick(service)

        service._store.set_watermark.assert_awaited_once_with(_NOW)


class TestExactlyOnce:
    @pytest.mark.asyncio
    async def test_skips_an_occurrence_another_replica_claimed(
        self, service: ScheduledAgentService, distributor: MagicMock
    ) -> None:
        await _run_tick(service, claimed=False)

        distributor.distribute_event.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_claims_before_firing(self, service: ScheduledAgentService) -> None:
        await _run_tick(service)

        service._store.claim_occurrence.assert_awaited_once_with(
            "ScheduledDemoAgent", "demo", datetime(2026, 8, 11, 12, tzinfo=UTC)
        )


class TestInstanceSelection:
    @pytest.mark.asyncio
    async def test_ignores_instances_without_a_schedule(
        self, service: ScheduledAgentService, distributor: MagicMock
    ) -> None:
        """A schedulable blueprint does not oblige every profile of it to be scheduled."""
        await _run_tick(service, configs=[_config(schedule=None)])

        distributor.distribute_event.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_fires_each_scheduled_instance(self, service: ScheduledAgentService, distributor: MagicMock) -> None:
        await _run_tick(service, configs=[_config(agent_id="a"), _config(agent_id="b"), _config(schedule=None)])

        fired = {call.kwargs["target_agent"].agent_id for call in distributor.distribute_event.call_args_list}
        assert fired == {"a", "b"}

    @pytest.mark.asyncio
    async def test_does_nothing_when_no_class_is_schedulable(
        self, service: ScheduledAgentService, distributor: MagicMock
    ) -> None:
        """An offline or non-schedulable class must not fire, even if a profile still carries a schedule."""
        await _run_tick(service, schedulable=False)

        distributor.distribute_event.assert_not_awaited()


class TestCatchUp:
    @pytest.mark.asyncio
    async def test_replays_occurrences_inside_the_catch_up_window(
        self, service: ScheduledAgentService, distributor: MagicMock
    ) -> None:
        await _run_tick(service, watermark=_NOW - timedelta(minutes=10))

        distributor.distribute_event.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_drops_occurrences_older_than_the_catch_up_window(
        self, service: ScheduledAgentService, distributor: MagicMock
    ) -> None:
        """After long downtime a stale watermark would otherwise produce a burst of runs whose
        scheduled moment has long passed."""
        await _run_tick(service, watermark=_NOW - timedelta(days=3))

        assert distributor.distribute_event.await_count == 1

    def test_clamps_the_window_start_to_the_catch_up_horizon(self, service: ScheduledAgentService) -> None:
        stale = _NOW - timedelta(days=3)

        assert service._clamp_window_start(stale, _NOW) == _NOW - timedelta(minutes=15)

    def test_keeps_a_recent_watermark(self, service: ScheduledAgentService) -> None:
        recent = _NOW - timedelta(minutes=1)

        assert service._clamp_window_start(recent, _NOW) == recent
