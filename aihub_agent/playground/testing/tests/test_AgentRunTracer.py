"""Tests for AgentRunTracer — OTEL + Langfuse span enrichment for agent runs."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aihub_lib.nats.events import StartEvent
from aihub_lib.nats.topics.agents.AgentInstanceTopic import AgentInstanceTopic
from bson import ObjectId
from opentelemetry.trace import StatusCode

from aihub_agent.tracing.AgentRunTracer import AgentRunTracer


@pytest.fixture
def mock_redis() -> AsyncMock:
    """Mock Redis client that stores data in a local dict."""
    redis_data: dict[str, bytes] = {}

    mock = AsyncMock()

    async def mock_get(key: str):
        return redis_data.get(key)

    async def mock_set(key: str, value: str, ex: int | None = None):
        redis_data[key] = value.encode() if isinstance(value, str) else value

    async def mock_delete(key: str):
        redis_data.pop(key, None)

    async def mock_scan(match: str = "*", count: int = 100):
        matching = [k.encode() for k in redis_data if k.startswith(match.replace("*", ""))]
        return (0, matching)

    mock.get = AsyncMock(side_effect=mock_get)
    mock.set = AsyncMock(side_effect=mock_set)
    mock.delete = AsyncMock(side_effect=mock_delete)
    mock.scan = AsyncMock(side_effect=mock_scan)
    return mock


@pytest.fixture
def tracer(mock_redis: AsyncMock) -> AgentRunTracer:
    return AgentRunTracer(mock_redis)


@pytest.fixture
def topic() -> AgentInstanceTopic:
    return AgentInstanceTopic(
        agent_class="TestAgent",
        agent_id="test-1",
        thread_id=str(ObjectId()),
        run_id=str(ObjectId()),
        display_id=str(ObjectId()),
        event_id=str(ObjectId()),
        event_type="control_event",
        event_name="StartEvent",
    )


class TestTraceRunStart:
    """Tests for trace_run_start — stores per-run metadata in Redis."""

    @pytest.mark.asyncio
    async def test_stores_user_query_for_user_message(
        self, tracer: AgentRunTracer, topic: AgentInstanceTopic, mock_redis: AsyncMock
    ) -> None:
        event = MagicMock(spec=StartEvent)
        event.is_user_message_event = True
        event.user_query = "Hello world"
        event.user = MagicMock()
        event.user.id = "user-42"

        with patch("aihub_agent.tracing.AgentRunTracer.get_step_parent_context", return_value=None):
            await tracer.trace_run_start(topic, event)

        # Verify Redis was called for input and user_id
        assert mock_redis.set.call_count >= 2

    @pytest.mark.asyncio
    async def test_stores_empty_for_non_user_message(
        self, tracer: AgentRunTracer, topic: AgentInstanceTopic, mock_redis: AsyncMock
    ) -> None:
        event = MagicMock(spec=StartEvent)
        event.is_user_message_event = False

        with patch("aihub_agent.tracing.AgentRunTracer.get_step_parent_context", return_value=None):
            await tracer.trace_run_start(topic, event)

        assert mock_redis.set.call_count >= 2


class TestTraceStepStart:
    """Tests for trace_step_start — creates OTEL spans with context propagation."""

    @pytest.mark.asyncio
    async def test_creates_span_with_attributes(self, tracer: AgentRunTracer, topic: AgentInstanceTopic) -> None:
        mock_span = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.start_span.return_value = mock_span
        tracer.tracer = mock_tracer

        async def dummy_step():
            pass

        with (
            patch("aihub_agent.tracing.AgentRunTracer.set_span_in_context"),
            patch("aihub_agent.tracing.AgentRunTracer.context") as mock_ctx,
        ):
            mock_ctx.attach.return_value = "token"

            async with tracer.trace_step_start(topic, dummy_step, {"arg": "val"}) as span:
                assert span is mock_span

        mock_tracer.start_span.assert_called_once()
        mock_span.end.assert_called_once()

    @pytest.mark.asyncio
    async def test_detaches_context_on_exception(self, tracer: AgentRunTracer, topic: AgentInstanceTopic) -> None:
        mock_span = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.start_span.return_value = mock_span
        tracer.tracer = mock_tracer

        async def dummy_step():
            pass

        with (
            patch("aihub_agent.tracing.AgentRunTracer.set_span_in_context"),
            patch("aihub_agent.tracing.AgentRunTracer.context") as mock_ctx,
        ):
            mock_ctx.attach.return_value = "token"

            with pytest.raises(ValueError):
                async with tracer.trace_step_start(topic, dummy_step, {}) as span:
                    raise ValueError("step failed")

            mock_ctx.detach.assert_called_once_with("token")
            mock_span.end.assert_called_once()


class TestTraceStepStop:
    """Tests for trace_step_stop — sets Langfuse trace-level span attributes."""

    @pytest.mark.asyncio
    async def test_sets_langfuse_trace_attributes(self, tracer: AgentRunTracer, topic: AgentInstanceTopic) -> None:
        # Store metadata via trace_run_start so Redis has the data
        event = MagicMock(spec=StartEvent)
        event.is_user_message_event = True
        event.user_query = "user question"
        event.user = MagicMock()
        event.user.id = "user-42"

        with patch("aihub_agent.tracing.AgentRunTracer.get_step_parent_context", return_value=None):
            await tracer.trace_run_start(topic, event)

        mock_span = MagicMock()

        await tracer.trace_step_stop(mock_span, None, topic)

        mock_span.set_attributes.assert_called_once()
        attrs = mock_span.set_attributes.call_args[0][0]

        assert attrs["langfuse.trace.name"] == f"🤖 {topic.agent_class}/{topic.agent_id}"
        assert attrs["langfuse.trace.input"] == "user question"
        assert attrs["langfuse.user.id"] == "user-42"
        assert attrs["langfuse.session.id"] == topic.thread_id
        mock_span.set_status.assert_called_once_with(StatusCode.OK)

    @pytest.mark.asyncio
    async def test_sets_output_on_final_step(self, tracer: AgentRunTracer, topic: AgentInstanceTopic) -> None:
        # Store empty input/user via trace_run_start
        event = MagicMock(spec=StartEvent)
        event.is_user_message_event = False
        with patch("aihub_agent.tracing.AgentRunTracer.get_step_parent_context", return_value=None):
            await tracer.trace_run_start(topic, event)

        # Simulate a semantic event that caches output
        semantic_event = MagicMock()
        semantic_event.is_stop_event = False
        semantic_event.is_semantic_event = True
        semantic_event.to_trace_dict.return_value = {"type": "llm"}
        semantic_event.to_semantic_convention.return_value = {}
        semantic_event.output_messages = [MagicMock(content="final answer")]
        semantic_event.token_count_prompt = None
        semantic_event.token_count_completion = None

        mock_span = MagicMock()
        await tracer.trace_step_stop(mock_span, [semantic_event], topic)

        # Now test the final step reads the cached output
        stop_event = MagicMock()
        stop_event.is_stop_event = True
        stop_event.is_semantic_event = False
        stop_event.to_trace_dict.return_value = {"type": "stop"}

        mock_span2 = MagicMock()
        await tracer.trace_step_stop(mock_span2, [stop_event], topic)

        attrs = mock_span2.set_attributes.call_args_list[-1][0][0]
        assert attrs["langfuse.trace.output"] == "final answer"


class TestTraceStepError:
    """Tests for trace_step_error — marks span as errored."""

    def test_sets_error_status(self, tracer: AgentRunTracer) -> None:
        mock_span = MagicMock()
        error = RuntimeError("something broke")

        tracer.trace_step_error(mock_span, error)

        mock_span.set_status.assert_called_once_with(StatusCode.ERROR, "something broke")
