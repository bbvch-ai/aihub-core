from fnmatch import fnmatch
from unittest.mock import AsyncMock

import pytest
from redis.asyncio import Redis

from swiss_ai_hub.core.dispatcher.stores.step.step_store import StepStore

EXECUTION_CONTEXT_ID = "6a59cd2bd5bc0adda65ab4e6"


@pytest.fixture
def redis_data() -> dict[str, bytes]:
    return {}


@pytest.fixture
def redis_client(redis_data: dict[str, bytes]) -> AsyncMock:
    mock_redis = AsyncMock(spec=Redis)

    async def mock_get(key):
        return redis_data.get(key)

    async def mock_set(key, value, ex=None):
        redis_data[key] = value.encode() if isinstance(value, str) else value
        return True

    def mock_scan_iter(match=None, count=None):
        async def _iter():
            for key in list(redis_data):
                if match is None or fnmatch(key, match):
                    yield key

        return _iter()

    async def mock_delete(*keys):
        return sum(1 for key in keys if redis_data.pop(key, None) is not None)

    async def mock_incrby(key, amount):
        value = int(redis_data.get(key, b"0")) + amount
        redis_data[key] = str(value).encode()
        return value

    async def mock_expire(key, ttl):
        return True

    mock_redis.get = mock_get
    mock_redis.set = mock_set
    # scan_iter/delete let StoreBase.delete_all actually run; without them it raises into
    # its own except-and-log and silently deletes nothing, so ordering tests pass vacuously.
    mock_redis.scan_iter = mock_scan_iter
    mock_redis.delete = mock_delete
    mock_redis.incrby = mock_incrby
    mock_redis.expire = mock_expire
    return mock_redis


@pytest.fixture
def step_store(redis_client: AsyncMock) -> StepStore:
    return StepStore(redis_client)


class TestCompletedMarker:
    @pytest.mark.asyncio
    async def test_unmarked_execution_context_is_not_completed(self, step_store: StepStore):
        assert await step_store.is_execution_context_completed(EXECUTION_CONTEXT_ID) is False

    @pytest.mark.asyncio
    async def test_marked_execution_context_is_completed(self, step_store: StepStore):
        await step_store.mark_execution_context_as_completed(EXECUTION_CONTEXT_ID)
        assert await step_store.is_execution_context_completed(EXECUTION_CONTEXT_ID) is True

    @pytest.mark.asyncio
    async def test_completed_marker_is_scoped_to_execution_context(self, step_store: StepStore):
        await step_store.mark_execution_context_as_completed(EXECUTION_CONTEXT_ID)
        assert await step_store.is_execution_context_completed("other-context") is False

    @pytest.mark.asyncio
    async def test_completed_marker_uses_namespaced_key(self, step_store: StepStore, redis_data: dict[str, bytes]):
        await step_store.mark_execution_context_as_completed(EXECUTION_CONTEXT_ID)
        assert redis_data == {f"step_markers:{EXECUTION_CONTEXT_ID}:completed": b"true"}

    @pytest.mark.asyncio
    async def test_completed_marker_is_independent_of_crashed_marker(self, step_store: StepStore):
        await step_store.mark_execution_context_as_completed(EXECUTION_CONTEXT_ID)
        assert await step_store.is_execution_context_crashed(EXECUTION_CONTEXT_ID) is False


class TestMarkersSurviveDeleteAll:
    """Markers record that a run is finished, so ``delete_all`` must not be able to reach them.
    They live under ``step_markers:{id}:*``, outside the ``steps:{id}:*`` glob teardown clears —
    which is what makes duplicate-delivery detection independent of the order of those calls."""

    @pytest.mark.asyncio
    async def test_delete_all_leaves_the_completed_marker_intact(self, step_store: StepStore):
        await step_store.mark_execution_context_as_completed(EXECUTION_CONTEXT_ID)

        await step_store.delete_all(EXECUTION_CONTEXT_ID)

        assert await step_store.is_execution_context_completed(EXECUTION_CONTEXT_ID) is True

    @pytest.mark.asyncio
    async def test_delete_all_leaves_the_crashed_marker_intact(self, step_store: StepStore):
        await step_store.mark_execution_context_as_crashed(EXECUTION_CONTEXT_ID)

        await step_store.delete_all(EXECUTION_CONTEXT_ID)

        assert await step_store.is_execution_context_crashed(EXECUTION_CONTEXT_ID) is True

    @pytest.mark.asyncio
    async def test_marker_survives_regardless_of_order_relative_to_delete_all(self, step_store: StepStore):
        """Marking before or after teardown must both leave a readable marker."""
        await step_store.mark_execution_context_as_completed(EXECUTION_CONTEXT_ID)
        await step_store.delete_all(EXECUTION_CONTEXT_ID)
        assert await step_store.is_execution_context_completed(EXECUTION_CONTEXT_ID) is True

        await step_store.delete_all("other-context")
        await step_store.mark_execution_context_as_completed("other-context")
        assert await step_store.is_execution_context_completed("other-context") is True

    @pytest.mark.asyncio
    async def test_delete_all_still_clears_step_data(self, step_store: StepStore):
        """Only the markers are exempt — step counters must still be cleared at teardown."""
        await step_store.increment_execution_count(EXECUTION_CONTEXT_ID, "some_step")
        await step_store.mark_execution_context_as_completed(EXECUTION_CONTEXT_ID)

        await step_store.delete_all(EXECUTION_CONTEXT_ID)

        assert await step_store.get_execution_count(EXECUTION_CONTEXT_ID, "some_step") == 0
        assert await step_store.is_execution_context_completed(EXECUTION_CONTEXT_ID) is True

    @pytest.mark.asyncio
    async def test_delete_all_leaves_other_execution_contexts_alone(self, step_store: StepStore):
        await step_store.mark_execution_context_as_completed(EXECUTION_CONTEXT_ID)
        await step_store.mark_execution_context_as_completed("other-context")

        await step_store.delete_all(EXECUTION_CONTEXT_ID)

        assert await step_store.is_execution_context_completed("other-context") is True
