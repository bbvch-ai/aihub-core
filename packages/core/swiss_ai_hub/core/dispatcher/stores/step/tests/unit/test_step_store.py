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

    mock_redis.get = mock_get
    mock_redis.set = mock_set
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
        assert redis_data == {f"steps:{EXECUTION_CONTEXT_ID}:completed": b"true"}

    @pytest.mark.asyncio
    async def test_completed_marker_is_independent_of_crashed_marker(self, step_store: StepStore):
        await step_store.mark_execution_context_as_completed(EXECUTION_CONTEXT_ID)
        assert await step_store.is_execution_context_crashed(EXECUTION_CONTEXT_ID) is False
