"""Tests for AgentRunTracer — OTEL + Langfuse span enrichment for agent runs."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aihub_lib.nats.events import StartEvent
from aihub_lib.nats.topics.agents.AgentInstanceTopic import AgentInstanceTopic
from bson import ObjectId
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes
from opentelemetry import trace
from opentelemetry.trace import NonRecordingSpan, SpanContext, StatusCode, TraceFlags

from aihub_agent.context.run.RunContext import RunContext
from aihub_agent.tracing.AgentRunTracer import (
    _TRACE_AITL_PARENT_CONTEXT_KEY,
    _TRACE_AITL_TARGET_AGENT_CLASS_KEY,
    _TRACE_RUN_CONTEXT_KEY,
    AgentRunTracer,
)

_FAKE_TRACEPARENT = {"traceparent": "00-0000000000000000000000000000dead-000000000000beef-01"}


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

        await tracer.trace_run_start(topic, event)

        run_context = RunContext.for_topic(mock_redis, topic)
        assert await run_context.get("_trace_input") == "Hello world"
        assert await run_context.get("_trace_user_id") == "user-42"

    @pytest.mark.asyncio
    async def test_stores_empty_for_non_user_message(
        self, tracer: AgentRunTracer, topic: AgentInstanceTopic, mock_redis: AsyncMock
    ) -> None:
        event = MagicMock(spec=StartEvent)
        event.is_user_message_event = False

        await tracer.trace_run_start(topic, event)

        run_context = RunContext.for_topic(mock_redis, topic)
        assert await run_context.get("_trace_input") == ""
        assert await run_context.get("_trace_user_id") == ""

    @pytest.mark.asyncio
    async def test_stores_trace_context_carrier(
        self, tracer: AgentRunTracer, topic: AgentInstanceTopic, mock_redis: AsyncMock
    ) -> None:
        event = MagicMock(spec=StartEvent)
        event.is_user_message_event = False

        await tracer.trace_run_start(topic, event)

        run_context = RunContext.for_topic(mock_redis, topic)
        carrier = await run_context.get(_TRACE_RUN_CONTEXT_KEY)
        assert carrier is not None
        assert isinstance(carrier, dict)


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
                async with tracer.trace_step_start(topic, dummy_step, {}) as _:
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
        semantic_event.token_count_total = None

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


class TestAitlWrapperSpan:
    """Tests for start_aitl_wrapper_span / end_aitl_wrapper_span — AITL bridge spans."""

    @pytest.fixture
    def caller_topic(self) -> AgentInstanceTopic:
        return AgentInstanceTopic(
            agent_class="OrchestratorAgent",
            agent_id="orch-1",
            thread_id=str(ObjectId()),
            run_id=str(ObjectId()),
            display_id=str(ObjectId()),
            event_id=str(ObjectId()),
            event_type="control_event",
            event_name="StartEvent",
        )

    @pytest.mark.asyncio
    async def test_creates_span_with_agent_kind(self, tracer: AgentRunTracer, caller_topic: AgentInstanceTopic) -> None:
        mock_span = MagicMock()
        mock_span.get_span_context.return_value = MagicMock(trace_id=1, span_id=2)
        mock_tracer = MagicMock()
        mock_tracer.start_span.return_value = mock_span
        tracer.tracer = mock_tracer

        span = await tracer.start_aitl_wrapper_span(
            caller_topic=caller_topic,
            target_agent_class="WorkerAgent",
            target_agent_id="worker-1",
            target_run_id=str(ObjectId()),
            target_thread_id=caller_topic.thread_id,
        )

        assert span is mock_span
        call_kwargs = mock_tracer.start_span.call_args
        attrs = call_kwargs.kwargs["attributes"]
        assert attrs[SpanAttributes.OPENINFERENCE_SPAN_KIND] == OpenInferenceSpanKindValues.AGENT.value
        assert "AITL -> WorkerAgent/worker-1" == call_kwargs.kwargs["name"]

    @pytest.mark.asyncio
    async def test_stores_trace_context_in_redis(
        self, tracer: AgentRunTracer, caller_topic: AgentInstanceTopic, mock_redis: AsyncMock
    ) -> None:
        real_span_context = SpanContext(
            trace_id=0xABCD, span_id=0x1234, is_remote=False, trace_flags=TraceFlags(TraceFlags.SAMPLED)
        )
        real_span = NonRecordingSpan(real_span_context)
        mock_tracer = MagicMock()
        mock_tracer.start_span.return_value = real_span
        tracer.tracer = mock_tracer

        target_run_id = str(ObjectId())
        target_thread_id = caller_topic.thread_id

        await tracer.start_aitl_wrapper_span(
            caller_topic=caller_topic,
            target_agent_class="WorkerAgent",
            target_agent_id="worker-1",
            target_run_id=target_run_id,
            target_thread_id=target_thread_id,
        )

        target_topic = AgentInstanceTopic(
            agent_class="WorkerAgent",
            agent_id="worker-1",
            thread_id=target_thread_id,
            run_id=target_run_id,
            display_id=caller_topic.display_id,
            event_id=caller_topic.event_id,
            event_type="control_event",
            event_name="StartEvent",
        )
        target_ctx = RunContext.for_topic(mock_redis, target_topic)
        carrier = await target_ctx.get(_TRACE_AITL_PARENT_CONTEXT_KEY)
        assert carrier is not None
        assert "traceparent" in carrier
        assert await target_ctx.get(_TRACE_AITL_TARGET_AGENT_CLASS_KEY) == "WorkerAgent"

    def test_end_sets_ok_status(self, tracer: AgentRunTracer) -> None:
        mock_span = MagicMock()
        tracer.end_aitl_wrapper_span(mock_span, success=True)
        mock_span.set_status.assert_called_once_with(StatusCode.OK)
        mock_span.end.assert_called_once()

    def test_end_sets_error_status(self, tracer: AgentRunTracer) -> None:
        mock_span = MagicMock()
        tracer.end_aitl_wrapper_span(mock_span, success=False)
        mock_span.set_status.assert_called_once_with(StatusCode.ERROR, "Delegated agent failed")
        mock_span.end.assert_called_once()


class TestAitlParentContext:
    """Tests for _get_aitl_parent_context — reconstructs parent span for AITL delegation."""

    @pytest.mark.asyncio
    async def test_returns_none_when_no_aitl_keys(self, tracer: AgentRunTracer, topic: AgentInstanceTopic) -> None:
        result = await tracer._get_aitl_parent_context(topic)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_context_when_aitl_keys_exist(
        self, tracer: AgentRunTracer, topic: AgentInstanceTopic, mock_redis: AsyncMock
    ) -> None:
        run_context = RunContext.for_topic(mock_redis, topic)
        await run_context.set(_TRACE_AITL_PARENT_CONTEXT_KEY, _FAKE_TRACEPARENT)
        await run_context.set(_TRACE_AITL_TARGET_AGENT_CLASS_KEY, topic.agent_class)

        result = await tracer._get_aitl_parent_context(topic)

        assert result is not None

    @pytest.mark.asyncio
    async def test_returns_none_when_agent_class_mismatch(
        self, tracer: AgentRunTracer, topic: AgentInstanceTopic, mock_redis: AsyncMock
    ) -> None:
        """Handles share_run_id=True where both agents share a RunContext."""
        run_context = RunContext.for_topic(mock_redis, topic)
        await run_context.set(_TRACE_AITL_PARENT_CONTEXT_KEY, _FAKE_TRACEPARENT)
        await run_context.set(_TRACE_AITL_TARGET_AGENT_CLASS_KEY, "DifferentAgent")

        result = await tracer._get_aitl_parent_context(topic)
        assert result is None


class TestTraceStepStartAitl:
    """Tests for trace_step_start with AITL parent context."""

    @pytest.mark.asyncio
    async def test_uses_aitl_parent_context_when_available(
        self, tracer: AgentRunTracer, topic: AgentInstanceTopic, mock_redis: AsyncMock
    ) -> None:
        run_context = RunContext.for_topic(mock_redis, topic)
        await run_context.set(_TRACE_AITL_PARENT_CONTEXT_KEY, _FAKE_TRACEPARENT)
        await run_context.set(_TRACE_AITL_TARGET_AGENT_CLASS_KEY, topic.agent_class)

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

            async with tracer.trace_step_start(topic, dummy_step, {}) as span:
                assert span is mock_span

        call_kwargs = mock_tracer.start_span.call_args
        assert call_kwargs.kwargs.get("context") is not None


class TestTraceStepStopAitl:
    """Tests for trace_step_stop with AITL delegation."""

    @pytest.mark.asyncio
    async def test_suppresses_langfuse_trace_attrs_for_aitl_delegated(
        self, tracer: AgentRunTracer, topic: AgentInstanceTopic, mock_redis: AsyncMock
    ) -> None:
        event = MagicMock(spec=StartEvent)
        event.is_user_message_event = False
        await tracer.trace_run_start(topic, event)

        run_context = RunContext.for_topic(mock_redis, topic)
        await run_context.set(_TRACE_AITL_PARENT_CONTEXT_KEY, _FAKE_TRACEPARENT)
        await run_context.set(_TRACE_AITL_TARGET_AGENT_CLASS_KEY, topic.agent_class)

        mock_span = MagicMock()
        await tracer.trace_step_stop(mock_span, None, topic)

        attrs = mock_span.set_attributes.call_args[0][0]
        assert "langfuse.trace.name" not in attrs
        assert "langfuse.trace.input" not in attrs
        assert "langfuse.trace.output" not in attrs
        assert "langfuse.user.id" not in attrs

    @pytest.mark.asyncio
    async def test_still_sets_session_id_for_aitl_delegated(
        self, tracer: AgentRunTracer, topic: AgentInstanceTopic, mock_redis: AsyncMock
    ) -> None:
        event = MagicMock(spec=StartEvent)
        event.is_user_message_event = False
        await tracer.trace_run_start(topic, event)

        run_context = RunContext.for_topic(mock_redis, topic)
        await run_context.set(_TRACE_AITL_PARENT_CONTEXT_KEY, _FAKE_TRACEPARENT)
        await run_context.set(_TRACE_AITL_TARGET_AGENT_CLASS_KEY, topic.agent_class)

        mock_span = MagicMock()
        await tracer.trace_step_stop(mock_span, None, topic)

        attrs = mock_span.set_attributes.call_args[0][0]
        assert attrs["langfuse.session.id"] == topic.thread_id
        assert attrs["deployment.environment.name"] == "agent"


class TestGetStepParentContext:
    """Tests for _get_step_parent_context — resolves parent context with AITL > run-start > None priority."""

    @pytest.mark.asyncio
    async def test_returns_none_when_no_context_stored(self, tracer: AgentRunTracer, topic: AgentInstanceTopic) -> None:
        result = await tracer._get_step_parent_context(topic)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_run_context_when_no_aitl_keys(
        self, tracer: AgentRunTracer, topic: AgentInstanceTopic, mock_redis: AsyncMock
    ) -> None:
        run_context = RunContext.for_topic(mock_redis, topic)
        await run_context.set(_TRACE_RUN_CONTEXT_KEY, _FAKE_TRACEPARENT)

        result = await tracer._get_step_parent_context(topic)

        assert result is not None

    @pytest.mark.asyncio
    async def test_aitl_takes_precedence_over_run_context(
        self, tracer: AgentRunTracer, topic: AgentInstanceTopic, mock_redis: AsyncMock
    ) -> None:
        """When both AITL and run-start contexts exist, AITL wins."""
        run_context = RunContext.for_topic(mock_redis, topic)

        aitl_carrier = {"traceparent": "00-00000000000000000000000000aaaa00-000000000000aa00-01"}
        run_carrier = {"traceparent": "00-00000000000000000000000000bbbb00-000000000000bb00-01"}

        await run_context.set(_TRACE_AITL_PARENT_CONTEXT_KEY, aitl_carrier)
        await run_context.set(_TRACE_AITL_TARGET_AGENT_CLASS_KEY, topic.agent_class)
        await run_context.set(_TRACE_RUN_CONTEXT_KEY, run_carrier)

        result = await tracer._get_step_parent_context(topic)

        assert result is not None
        span = trace.get_current_span(result)
        span_ctx = span.get_span_context()
        assert span_ctx.trace_id == 0xAAAA00
        assert span_ctx.span_id == 0xAA00

    @pytest.mark.asyncio
    async def test_falls_through_to_run_context_when_aitl_class_mismatch(
        self, tracer: AgentRunTracer, topic: AgentInstanceTopic, mock_redis: AsyncMock
    ) -> None:
        """share_run_id=True: AITL keys exist but target a different agent class."""
        run_context = RunContext.for_topic(mock_redis, topic)

        aitl_carrier = {"traceparent": "00-00000000000000000000000000aaaa00-000000000000aa00-01"}
        run_carrier = {"traceparent": "00-00000000000000000000000000bbbb00-000000000000bb00-01"}

        await run_context.set(_TRACE_AITL_PARENT_CONTEXT_KEY, aitl_carrier)
        await run_context.set(_TRACE_AITL_TARGET_AGENT_CLASS_KEY, "DifferentAgent")
        await run_context.set(_TRACE_RUN_CONTEXT_KEY, run_carrier)

        result = await tracer._get_step_parent_context(topic)

        assert result is not None
        span = trace.get_current_span(result)
        span_ctx = span.get_span_context()
        assert span_ctx.trace_id == 0xBBBB00
        assert span_ctx.span_id == 0xBB00


class TestTraceStepStartRunContext:
    """Tests for trace_step_start using saved run context as parent."""

    @pytest.mark.asyncio
    async def test_uses_run_context_as_parent_when_available(
        self, tracer: AgentRunTracer, topic: AgentInstanceTopic, mock_redis: AsyncMock
    ) -> None:
        run_context = RunContext.for_topic(mock_redis, topic)
        await run_context.set(_TRACE_RUN_CONTEXT_KEY, _FAKE_TRACEPARENT)

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

            async with tracer.trace_step_start(topic, dummy_step, {}) as span:
                assert span is mock_span

        call_kwargs = mock_tracer.start_span.call_args
        assert call_kwargs.kwargs.get("context") is not None

    @pytest.mark.asyncio
    async def test_uses_none_context_when_no_run_context(
        self, tracer: AgentRunTracer, topic: AgentInstanceTopic
    ) -> None:
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

            async with tracer.trace_step_start(topic, dummy_step, {}) as span:
                assert span is mock_span

        call_kwargs = mock_tracer.start_span.call_args
        assert call_kwargs.kwargs.get("context") is None
