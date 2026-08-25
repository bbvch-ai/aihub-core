from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from redis.exceptions import LockError

from swiss_ai_hub.core.scheduling.schedule_state_store import ScheduleStateStore

_OCCURRENCE = datetime(2026, 8, 11, 12, tzinfo=UTC)


def _make_lock(*, acquired: bool, release_error: Exception | None = None) -> MagicMock:
    lock = MagicMock()
    lock.acquire = AsyncMock(return_value=acquired)
    lock.release = AsyncMock(side_effect=release_error)
    return lock


def _make_store(redis: MagicMock, key_prefix: str | None = None) -> ScheduleStateStore:
    prefix = {"key_prefix": key_prefix} if key_prefix else {}
    return ScheduleStateStore(redis=redis, lease_ttl=120, claim_ttl=3600, **prefix)


@pytest.fixture
def mock_redis() -> MagicMock:
    redis = MagicMock()
    redis.set = AsyncMock(return_value=True)
    redis.get = AsyncMock(return_value=None)
    return redis


class TestLeadership:
    @pytest.mark.asyncio
    async def test_yields_true_when_the_lease_is_free(self, mock_redis: MagicMock) -> None:
        mock_redis.lock.return_value = _make_lock(acquired=True)

        async with _make_store(mock_redis).leadership() as is_leader:
            assert is_leader

    @pytest.mark.asyncio
    async def test_yields_false_when_another_replica_holds_the_lease(self, mock_redis: MagicMock) -> None:
        """The loser skips the tick rather than queueing — the holder covers the same window."""
        mock_redis.lock.return_value = _make_lock(acquired=False)

        async with _make_store(mock_redis).leadership() as is_leader:
            assert not is_leader

    @pytest.mark.asyncio
    async def test_releases_the_lease_after_the_tick(self, mock_redis: MagicMock) -> None:
        lock = _make_lock(acquired=True)
        mock_redis.lock.return_value = lock

        async with _make_store(mock_redis).leadership():
            pass

        lock.release.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_releases_the_lease_when_the_tick_raises(self, mock_redis: MagicMock) -> None:
        """A leader that crashed mid-tick must not keep the lease until its TTL expires."""
        lock = _make_lock(acquired=True)
        mock_redis.lock.return_value = lock

        with pytest.raises(RuntimeError, match="boom"):
            async with _make_store(mock_redis).leadership():
                raise RuntimeError("boom")

        lock.release.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_survives_a_lease_that_expired_mid_tick(self, mock_redis: MagicMock) -> None:
        """An expired lease means another replica may already hold it; that must not mask the tick."""
        mock_redis.lock.return_value = _make_lock(acquired=True, release_error=LockError("expired"))

        async with _make_store(mock_redis).leadership() as is_leader:
            assert is_leader

    @pytest.mark.asyncio
    async def test_does_not_release_a_lease_it_never_acquired(self, mock_redis: MagicMock) -> None:
        lock = _make_lock(acquired=False)
        mock_redis.lock.return_value = lock

        async with _make_store(mock_redis).leadership():
            pass

        lock.release.assert_not_awaited()


class TestClaimOccurrence:
    @pytest.mark.asyncio
    async def test_claims_an_unclaimed_occurrence(self, mock_redis: MagicMock) -> None:
        mock_redis.set = AsyncMock(return_value=True)

        assert await _make_store(mock_redis).claim_occurrence("Demo", "one", _OCCURRENCE)

    @pytest.mark.asyncio
    async def test_refuses_an_already_claimed_occurrence(self, mock_redis: MagicMock) -> None:
        """This is what makes a failover mid-tick safe: the takeover replica loses the SET NX race."""
        mock_redis.set = AsyncMock(return_value=None)

        assert not await _make_store(mock_redis).claim_occurrence("Demo", "one", _OCCURRENCE)

    @pytest.mark.asyncio
    async def test_claim_is_atomic_and_expiring(self, mock_redis: MagicMock) -> None:
        await _make_store(mock_redis).claim_occurrence("Demo", "one", _OCCURRENCE)

        _, kwargs = mock_redis.set.call_args
        assert kwargs["nx"] is True
        assert kwargs["ex"] == 3600

    @pytest.mark.asyncio
    async def test_claim_key_separates_instances_and_occurrences(self, mock_redis: MagicMock) -> None:
        store = _make_store(mock_redis)
        keys: list[str] = []
        mock_redis.set = AsyncMock(side_effect=lambda key, *_, **__: keys.append(key) or True)

        await store.claim_occurrence("Demo", "one", _OCCURRENCE)
        await store.claim_occurrence("Demo", "two", _OCCURRENCE)
        await store.claim_occurrence("Demo", "one", datetime(2026, 8, 11, 13, tzinfo=UTC))

        assert len(set(keys)) == 3


class TestWatermark:
    @pytest.mark.asyncio
    async def test_returns_none_on_a_cold_start(self, mock_redis: MagicMock) -> None:
        assert await _make_store(mock_redis).get_watermark() is None

    @pytest.mark.asyncio
    async def test_round_trips_through_redis(self, mock_redis: MagicMock) -> None:
        store = _make_store(mock_redis)
        await store.set_watermark(_OCCURRENCE)
        mock_redis.get = AsyncMock(return_value=mock_redis.set.call_args[0][1])

        assert await store.get_watermark() == _OCCURRENCE

    @pytest.mark.asyncio
    async def test_reads_a_bytes_response(self, mock_redis: MagicMock) -> None:
        """Redis clients configured without decode_responses hand back bytes."""
        mock_redis.get = AsyncMock(return_value=_OCCURRENCE.isoformat().encode())

        assert await _make_store(mock_redis).get_watermark() == _OCCURRENCE


class TestKeyPrefix:
    """The prefix is what lets a second scheduler coordinate on the same Redis — `RedisSettings` exposes
    only a URL, so there is no separate database for a test to move to."""

    @pytest.mark.asyncio
    async def test_the_default_prefix_keeps_existing_keys_byte_identical(self, mock_redis: MagicMock) -> None:
        """A changed default would orphan the watermark and every live claim on deploy."""
        await _make_store(mock_redis).set_watermark(_OCCURRENCE)

        assert mock_redis.set.call_args[0][0] == "scheduler:watermark"

    @pytest.mark.asyncio
    async def test_a_custom_prefix_namespaces_every_key(self, mock_redis: MagicMock) -> None:
        store = _make_store(mock_redis, key_prefix="itest:abc")

        await store.set_watermark(_OCCURRENCE)
        assert mock_redis.set.call_args[0][0] == "itest:abc:watermark"

        await store.claim_occurrence("CronDemoAgent", "demo", _OCCURRENCE)
        assert mock_redis.set.call_args[0][0].startswith("itest:abc:fired:")

        await store.claim_retention_window(3600)
        assert mock_redis.set.call_args[0][0] == "itest:abc:retention"

    @pytest.mark.asyncio
    async def test_the_leader_lease_is_namespaced_too(self, mock_redis: MagicMock) -> None:
        """Two stores sharing a lease key would defeat the point of isolating them."""
        mock_redis.lock = MagicMock(return_value=_make_lock(acquired=True))
        store = _make_store(mock_redis, key_prefix="itest:abc")

        async with store.leadership():
            pass

        assert mock_redis.lock.call_args[0][0] == "itest:abc:leader"


class TestRetentionWindow:
    @pytest.mark.asyncio
    async def test_claims_the_window_when_it_is_free(self, mock_redis: MagicMock) -> None:
        assert await _make_store(mock_redis).claim_retention_window(3600) is True

    @pytest.mark.asyncio
    async def test_refuses_a_window_another_replica_holds(self, mock_redis: MagicMock) -> None:
        """This is what keeps a bulk delete off the per-tick path, cluster-wide, with no second timer."""
        mock_redis.set = AsyncMock(return_value=None)

        assert await _make_store(mock_redis).claim_retention_window(3600) is False

    @pytest.mark.asyncio
    async def test_the_claim_expires_with_the_interval(self, mock_redis: MagicMock) -> None:
        await _make_store(mock_redis).claim_retention_window(1800)

        assert mock_redis.set.call_args.kwargs == {"nx": True, "ex": 1800}
