from unittest.mock import AsyncMock, MagicMock

import pytest

from aihub_mcp.translation.HITLPendingStore import DEFAULT_HITL_TTL_SECONDS, HITLPendingStore


class TestHITLPendingStore:
    """Tests for HITLPendingStore."""

    @pytest.fixture
    def mock_redis(self) -> MagicMock:
        """Create a mock Redis client."""
        redis = MagicMock()
        redis.setex = AsyncMock(return_value=True)
        redis.get = AsyncMock(return_value=None)
        redis.delete = AsyncMock(return_value=1)
        return redis

    @pytest.fixture
    def store(self, mock_redis: MagicMock) -> HITLPendingStore:
        """Create a HITLPendingStore with mock Redis."""
        return HITLPendingStore(mock_redis)

    def test_initialization(self, store: HITLPendingStore) -> None:
        """Test store initializes with correct prefix and TTL."""
        assert store.prefix == "pending_hitl"
        assert store.default_ttl == DEFAULT_HITL_TTL_SECONDS

    def test_custom_ttl(self, mock_redis: MagicMock) -> None:
        """Test store respects custom TTL."""
        custom_ttl = 300
        store = HITLPendingStore(mock_redis, ttl_seconds=custom_ttl)
        assert store.default_ttl == custom_ttl

    @pytest.mark.asyncio
    async def test_store_pending_creates_context(self, store: HITLPendingStore, mock_redis: MagicMock) -> None:
        """Test storing a pending HITL request."""
        request_id = "hitl_abc123"
        agent_class = "TestAgent"
        thread_id = "thread_123"
        display_id = "display_123"
        run_id = "run_123"
        request_event = {"question": "What is your name?", "hitl_type": "input"}
        hitl_type = "input"
        accumulated_content = ["Hello", "World"]

        # Mock put_json_value to return True
        store.put_json_value = AsyncMock(return_value=True)

        result = await store.store_pending(
            request_id=request_id,
            agent_class=agent_class,
            thread_id=thread_id,
            display_id=display_id,
            run_id=run_id,
            request_event=request_event,
            hitl_type=hitl_type,
            accumulated_content=accumulated_content,
        )

        assert result is True
        store.put_json_value.assert_called_once()

        # Verify the context structure
        call_args = store.put_json_value.call_args
        stored_context = call_args[0][2]  # Third positional arg is the context
        assert stored_context["request_id"] == request_id
        assert stored_context["agent_class"] == agent_class
        assert stored_context["thread_id"] == thread_id
        assert stored_context["display_id"] == display_id
        assert stored_context["run_id"] == run_id
        assert stored_context["request_event"] == request_event
        assert stored_context["hitl_type"] == hitl_type
        assert stored_context["accumulated_content"] == accumulated_content
        assert "created_at" in stored_context

    @pytest.mark.asyncio
    async def test_get_pending_returns_context(self, store: HITLPendingStore) -> None:
        """Test retrieving a pending HITL request."""
        request_id = "hitl_abc123"
        expected_context = {
            "request_id": request_id,
            "agent_class": "TestAgent",
            "thread_id": "thread_123",
            "hitl_type": "input",
        }

        store.get_json_value = AsyncMock(return_value=expected_context)

        result = await store.get_pending(request_id)

        assert result == expected_context
        store.get_json_value.assert_called_once_with(request_id, "context")

    @pytest.mark.asyncio
    async def test_get_pending_returns_none_when_not_found(self, store: HITLPendingStore) -> None:
        """Test retrieving a non-existent pending request returns None."""
        store.get_json_value = AsyncMock(return_value=None)

        result = await store.get_pending("nonexistent_id")

        assert result is None

    @pytest.mark.asyncio
    async def test_remove_pending_deletes_context(self, store: HITLPendingStore) -> None:
        """Test removing a pending HITL request."""
        request_id = "hitl_abc123"
        store.delete_all = AsyncMock()

        await store.remove_pending(request_id)

        store.delete_all.assert_called_once_with(request_id)


class TestHITLPendingStoreKeyFormat:
    """Tests for key format and naming conventions."""

    def test_key_prefix_is_pending_hitl(self) -> None:
        """Verify the key prefix follows the convention."""
        mock_redis = MagicMock()
        store = HITLPendingStore(mock_redis)
        assert store.prefix == "pending_hitl"

    def test_default_ttl_is_ten_minutes(self) -> None:
        """Verify default TTL is 10 minutes (600 seconds)."""
        assert DEFAULT_HITL_TTL_SECONDS == 60 * 10
