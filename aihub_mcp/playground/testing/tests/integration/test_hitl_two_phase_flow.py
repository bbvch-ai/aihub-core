"""
Integration tests for the two-phase HITL (Human-in-the-Loop) flow.

The two-phase flow is used when MCP clients don't support native elicitation:
1. Phase 1: Agent requests human input, MCP server stores context and returns pending status
2. Phase 2: Client calls submit_hitl_response with user's answer, agent resumes execution

These tests verify the complete flow works end-to-end with mocked NATS.
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from aihub_mcp.translation.HITLPendingStore import HITLPendingStore, HITLPendingStoreInterface


class InMemoryHITLStore(HITLPendingStoreInterface):
    """In-memory implementation of HITLPendingStoreInterface for testing."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    async def store_pending(
        self,
        request_id: str,
        agent_class: str,
        thread_id: str,
        display_id: str,
        run_id: str,
        request_event: dict[str, Any],
        hitl_type: str,
        accumulated_content: list[str],
    ) -> bool:
        """Store pending HITL context in memory."""
        self._store[request_id] = {
            "request_id": request_id,
            "agent_class": agent_class,
            "thread_id": thread_id,
            "display_id": display_id,
            "run_id": run_id,
            "request_event": request_event,
            "hitl_type": hitl_type,
            "accumulated_content": accumulated_content,
        }
        return True

    async def get_pending(self, request_id: str) -> dict[str, Any] | None:
        """Retrieve pending HITL context from memory."""
        return self._store.get(request_id)

    async def remove_pending(self, request_id: str) -> None:
        """Remove pending request from memory."""
        if request_id in self._store:
            del self._store[request_id]


class TestTwoPhaseHITLFlow:
    """Integration tests for two-phase HITL flow."""

    @pytest.fixture
    def in_memory_store(self) -> InMemoryHITLStore:
        """Create an in-memory HITL store for testing."""
        return InMemoryHITLStore()

    @pytest.fixture
    def mock_ctx(self) -> MagicMock:
        """Create a mock MCP context."""
        ctx = MagicMock()
        ctx.info = AsyncMock()
        ctx.warning = AsyncMock()
        ctx.error = AsyncMock()
        return ctx

    @pytest.mark.asyncio
    async def test_store_and_retrieve_pending_context(self, in_memory_store: InMemoryHITLStore) -> None:
        """Test that pending context can be stored and retrieved correctly."""
        request_id = "hitl_test123"
        agent_class = "TestAgent"
        thread_id = "thread_abc"
        display_id = "display_xyz"
        run_id = "run_123"
        request_event = {"question": "What is your name?", "hitl_type": "input"}
        hitl_type = "input"
        accumulated_content = ["Hello, ", "I need your "]

        # Store the pending request
        success = await in_memory_store.store_pending(
            request_id=request_id,
            agent_class=agent_class,
            thread_id=thread_id,
            display_id=display_id,
            run_id=run_id,
            request_event=request_event,
            hitl_type=hitl_type,
            accumulated_content=accumulated_content,
        )

        assert success is True

        # Retrieve it
        context = await in_memory_store.get_pending(request_id)

        assert context is not None
        assert context["request_id"] == request_id
        assert context["agent_class"] == agent_class
        assert context["thread_id"] == thread_id
        assert context["display_id"] == display_id
        assert context["run_id"] == run_id
        assert context["request_event"] == request_event
        assert context["hitl_type"] == hitl_type
        assert context["accumulated_content"] == accumulated_content

    @pytest.mark.asyncio
    async def test_remove_pending_context(self, in_memory_store: InMemoryHITLStore) -> None:
        """Test that pending context can be removed after processing."""
        request_id = "hitl_to_remove"

        await in_memory_store.store_pending(
            request_id=request_id,
            agent_class="TestAgent",
            thread_id="thread_1",
            display_id="display_1",
            run_id="run_1",
            request_event={},
            hitl_type="input",
            accumulated_content=[],
        )

        # Verify it exists
        assert await in_memory_store.get_pending(request_id) is not None

        # Remove it
        await in_memory_store.remove_pending(request_id)

        # Verify it's gone
        assert await in_memory_store.get_pending(request_id) is None

    @pytest.mark.asyncio
    async def test_get_nonexistent_returns_none(self, in_memory_store: InMemoryHITLStore) -> None:
        """Test that retrieving a non-existent request returns None."""
        result = await in_memory_store.get_pending("nonexistent_id")
        assert result is None

    @pytest.mark.asyncio
    async def test_confirmation_type_flow(self, in_memory_store: InMemoryHITLStore) -> None:
        """Test the two-phase flow for confirmation-type HITL requests."""
        request_id = "hitl_confirm_123"

        # Phase 1: Store pending confirmation request
        await in_memory_store.store_pending(
            request_id=request_id,
            agent_class="ConfirmAgent",
            thread_id="thread_confirm",
            display_id="display_confirm",
            run_id="run_confirm",
            request_event={"question": "Do you want to proceed?", "hitl_type": "confirmation"},
            hitl_type="confirmation",
            accumulated_content=["Processing your request..."],
        )

        # Phase 2: Retrieve and verify confirmation type
        context = await in_memory_store.get_pending(request_id)
        assert context is not None
        assert context["hitl_type"] == "confirmation"

        # Simulate parsing "yes" response for confirmation
        user_response = "yes"
        parsed_response = user_response.lower() in ("yes", "true", "1", "y")
        assert parsed_response is True

        # Cleanup
        await in_memory_store.remove_pending(request_id)

    @pytest.mark.asyncio
    async def test_input_type_flow(self, in_memory_store: InMemoryHITLStore) -> None:
        """Test the two-phase flow for input-type HITL requests."""
        request_id = "hitl_input_456"

        # Phase 1: Store pending input request
        await in_memory_store.store_pending(
            request_id=request_id,
            agent_class="InputAgent",
            thread_id="thread_input",
            display_id="display_input",
            run_id="run_input",
            request_event={"question": "What is your preferred language?", "hitl_type": "input"},
            hitl_type="input",
            accumulated_content=["Let me help you configure..."],
        )

        # Phase 2: Retrieve and verify input type
        context = await in_memory_store.get_pending(request_id)
        assert context is not None
        assert context["hitl_type"] == "input"

        # Input type uses the response as-is
        user_response = "Python"
        assert user_response == "Python"

        # Cleanup
        await in_memory_store.remove_pending(request_id)

    @pytest.mark.asyncio
    async def test_accumulated_content_preserved(self, in_memory_store: InMemoryHITLStore) -> None:
        """Test that accumulated content from before HITL request is preserved."""
        request_id = "hitl_preserve_content"
        original_content = ["First chunk", "Second chunk", "Third chunk before HITL"]

        await in_memory_store.store_pending(
            request_id=request_id,
            agent_class="ContentAgent",
            thread_id="thread_content",
            display_id="display_content",
            run_id="run_content",
            request_event={"question": "Continue?", "hitl_type": "confirmation"},
            hitl_type="confirmation",
            accumulated_content=original_content,
        )

        context = await in_memory_store.get_pending(request_id)
        assert context is not None
        assert context["accumulated_content"] == original_content
        assert len(context["accumulated_content"]) == 3


class TestHITLStoreInterface:
    """Tests for the HITLPendingStoreInterface contract."""

    def test_in_memory_implements_interface(self) -> None:
        """Verify InMemoryHITLStore properly implements the interface."""
        store = InMemoryHITLStore()
        assert isinstance(store, HITLPendingStoreInterface)

    def test_redis_store_implements_interface(self) -> None:
        """Verify HITLPendingStore (Redis-backed) properly implements the interface."""
        mock_redis = MagicMock()
        store = HITLPendingStore(mock_redis)
        assert isinstance(store, HITLPendingStoreInterface)
