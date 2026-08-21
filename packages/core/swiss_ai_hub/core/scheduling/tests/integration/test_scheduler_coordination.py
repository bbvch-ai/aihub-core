"""Exactly-once firing, proven against a real Valkey.

Every other scheduling test replaces `ScheduleStateStore` or its Redis with a mock, so the acceptance
criterion this feature exists to satisfy — N replicas, one run per occurrence — has only ever been
asserted as "we call SET with NX". These tests run two `CronScheduler` instances against the real thing,
including the failover case the per-occurrence claim exists for and which no unit test reaches.

Run with the dev stack up:
    cd packages/core && make test-integration

Marked `integration` by directory, so the default `make test` (-m unit) skips it.
"""

import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from redis.asyncio import Redis

from swiss_ai_hub.core.infrastructure.redis.redis_settings import RedisSettings
from swiss_ai_hub.core.scheduling.cron_schedule import CronSchedule
from swiss_ai_hub.core.scheduling.cron_scheduler import CronScheduler, _SchedulableSnapshot
from swiss_ai_hub.core.scheduling.scheduler_settings import SchedulerSettings

_MODULE = "swiss_ai_hub.core.scheduling.cron_scheduler"
_NOW = datetime(2026, 8, 11, 12, 0, 30, tzinfo=UTC)
_EVERY_MINUTE = CronSchedule(minute="*", hour="*", day_of_month="*", month="*", day_of_week="*", timezone="UTC")


def _profile() -> tuple[CronSchedule, SimpleNamespace]:
    return _EVERY_MINUTE, SimpleNamespace(agent_class="CronDemoAgent", agent_id="demo", config_data={})


@pytest_asyncio.fixture
async def redis() -> Redis:
    """Function-scoped on purpose: pytest-asyncio gives each test a fresh event loop, and a client
    cached across tests binds its connection pool to the first one."""
    client = RedisSettings.create_client()
    try:
        await client.ping()
    except Exception as unreachable:
        await client.aclose()
        pytest.skip(f"Redis is not reachable; start the dev stack ({unreachable})")
    yield client
    await client.aclose()


@pytest.fixture
def key_prefix() -> str:
    """A namespace of this test's own, so it cannot contend with a developer's running API — which does
    hold the real `scheduler:leader` key whenever the dev stack is up."""
    return f"itest:scheduler:{uuid4().hex[:8]}"


@pytest_asyncio.fixture(autouse=True)
async def _clean_keys(redis: Redis, key_prefix: str):
    yield
    keys = [key async for key in redis.scan_iter(match=f"{key_prefix}:*")]
    if keys:
        await redis.delete(*keys)


def _scheduler(redis: Redis, key_prefix: str, distributor: MagicMock) -> CronScheduler:
    scheduler = CronScheduler(
        redis=redis,
        external_agent_event_distributor=distributor,
        settings=SchedulerSettings(REDIS_KEY_PREFIX=key_prefix),
    )
    # Only Redis is real here — the point is the coordination, not the persistence reads.
    scheduler._load_schedulable_snapshot = lambda now, watermark: _SchedulableSnapshot(
        online=[_profile()],
        window_start=scheduler._clamp_window_start(watermark, now),
    )
    return scheduler


def _distributor() -> MagicMock:
    distributor = MagicMock()
    distributor.distribute_event = AsyncMock()
    return distributor


@pytest.fixture
def frozen_thread():
    with (
        patch(f"{_MODULE}.datetime", **{"now.return_value": _NOW}),
        patch(f"{_MODULE}.ThreadEntity.get_or_create_scheduled_thread", return_value=SimpleNamespace(id="thread-1")),
    ):
        yield


@pytest.mark.integration
@pytest.mark.asyncio
class TestTwoReplicasFireOnce:
    async def test_concurrent_ticks_fire_one_run(self, redis: Redis, key_prefix: str, frozen_thread) -> None:
        """The acceptance criterion: more than one API replica must not double-fire an occurrence.

        This one is carried by the *lease* — it still passes with the per-occurrence claim disabled,
        because only one replica ever gets to tick. The claim is what the two tests below cover. Keeping
        them separate is what makes it visible which mechanism has broken when one of them fails.

        Which replica wins is never asserted — both interleavings are correct, and pinning one would
        make the test flaky rather than stricter.
        """
        first, second = _distributor(), _distributor()
        a = _scheduler(redis, key_prefix, first)
        b = _scheduler(redis, key_prefix, second)
        # Without a watermark the first tick only adopts `now` and fires nothing.
        await a._store.set_watermark(_NOW - timedelta(seconds=90))

        await asyncio.gather(a._tick(), b._tick())

        fired = first.distribute_event.await_count + second.distribute_event.await_count
        assert fired == 1

    async def test_a_second_round_does_not_refire_the_same_occurrence(
        self, redis: Redis, key_prefix: str, frozen_thread
    ) -> None:
        """The claim outlives the tick, so a re-scanned window is not a re-run."""
        first, second = _distributor(), _distributor()
        a = _scheduler(redis, key_prefix, first)
        b = _scheduler(redis, key_prefix, second)
        await a._store.set_watermark(_NOW - timedelta(seconds=90))

        await asyncio.gather(a._tick(), b._tick())
        await a._store.set_watermark(_NOW - timedelta(seconds=90))
        await asyncio.gather(a._tick(), b._tick())

        fired = first.distribute_event.await_count + second.distribute_event.await_count
        assert fired == 1

    async def test_a_leader_dying_before_the_watermark_advances_does_not_duplicate(
        self, redis: Redis, key_prefix: str, frozen_thread
    ) -> None:
        """The case the per-occurrence claim exists for, and the one a leader lease alone cannot cover.

        The lease guarantees only that two replicas do not tick *concurrently*. A leader that fires and
        then dies leaves the watermark where it was, so the next leader legitimately re-scans the same
        window — and must find the occurrence already claimed.
        """
        first, second = _distributor(), _distributor()
        dying = _scheduler(redis, key_prefix, first)
        await dying._store.set_watermark(_NOW - timedelta(seconds=90))
        # Fire, then fail before the watermark moves — exactly what a crashed replica leaves behind.
        dying._store.set_watermark = AsyncMock(side_effect=RuntimeError("replica died"))
        with pytest.raises(RuntimeError):
            await dying._tick()

        successor = _scheduler(redis, key_prefix, second)
        await successor._tick()

        fired = first.distribute_event.await_count + second.distribute_event.await_count
        assert fired == 1

    async def test_an_independent_prefix_is_unaffected(self, redis: Redis, key_prefix: str, frozen_thread) -> None:
        """Isolation has to hold in both directions, or the test suite becomes the flake."""
        mine, theirs = _distributor(), _distributor()
        a = _scheduler(redis, key_prefix, mine)
        b = _scheduler(redis, f"{key_prefix}-other", theirs)
        await a._store.set_watermark(_NOW - timedelta(seconds=90))
        await b._store.set_watermark(_NOW - timedelta(seconds=90))

        await asyncio.gather(a._tick(), b._tick())

        assert mine.distribute_event.await_count == 1
        assert theirs.distribute_event.await_count == 1
        keys = [key async for key in redis.scan_iter(match=f"{key_prefix}-other:*")]
        await redis.delete(*keys)


@pytest.mark.integration
@pytest.mark.asyncio
class TestTheLeaderLease:
    async def test_only_one_replica_holds_the_lease_at_a_time(self, redis: Redis, key_prefix: str) -> None:
        a = _scheduler(redis, key_prefix, _distributor())
        b = _scheduler(redis, key_prefix, _distributor())

        async with a._store.leadership() as a_is_leader:
            async with b._store.leadership() as b_is_leader:
                assert (a_is_leader, b_is_leader) == (True, False)

    async def test_the_lease_is_released_for_the_next_tick(self, redis: Redis, key_prefix: str) -> None:
        """A lease that outlived its tick would stall the scheduler until the TTL expired."""
        scheduler = _scheduler(redis, key_prefix, _distributor())

        async with scheduler._store.leadership() as first:
            assert first is True
        async with scheduler._store.leadership() as second:
            assert second is True

    async def test_the_retention_window_is_claimed_once_per_interval(self, redis: Redis, key_prefix: str) -> None:
        scheduler = _scheduler(redis, key_prefix, _distributor())

        assert await scheduler._store.claim_retention_window(60) is True
        assert await scheduler._store.claim_retention_window(60) is False
