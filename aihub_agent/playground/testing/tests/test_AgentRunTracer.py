"""Tests for AgentRunTracer — OTEL + Langfuse span enrichment for agent runs."""

from unittest.mock import MagicMock, patch

import pytest
from aihub_lib.nats.events import StartEvent
from aihub_lib.nats.topics.agents.AgentInstanceTopic import AgentInstanceTopic
from bson import ObjectId
from opentelemetry.trace import StatusCode

from aihub_agent.tracing.AgentRunTracer import _CACHE_MAX_SIZE, _CACHE_TTL_SECONDS, AgentRunTracer


@pytest.fixture
def tracer() -> AgentRunTracer:
    return AgentRunTracer()


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


class TestTTLCacheConfiguration:
    """Verify that run metadata uses TTLCache (prevents memory leaks)."""

    def test_caches_have_correct_max_size(self, tracer: AgentRunTracer) -> None:
        assert tracer._run_inputs.maxsize == _CACHE_MAX_SIZE
        assert tracer._run_user_ids.maxsize == _CACHE_MAX_SIZE
        assert tracer._run_outputs.maxsize == _CACHE_MAX_SIZE

    def test_caches_have_correct_ttl(self, tracer: AgentRunTracer) -> None:
        assert tracer._run_inputs.ttl == _CACHE_TTL_SECONDS
        assert tracer._run_user_ids.ttl == _CACHE_TTL_SECONDS
        assert tracer._run_outputs.ttl == _CACHE_TTL_SECONDS


class TestTraceRunStart:
    """Tests for trace_run_start — stores per-run metadata."""

    @pytest.mark.asyncio
    async def test_stores_user_query_for_user_message(self, tracer: AgentRunTracer, topic: AgentInstanceTopic) -> None:
        event = MagicMock(spec=StartEvent)
        event.is_user_message_event = True
        event.user_query = "Hello world"
        event.user = MagicMock()
        event.user.id = "user-42"

        await tracer.trace_run_start(topic, event)

        assert tracer._run_inputs[topic.run_id] == "Hello world"
        assert tracer._run_user_ids[topic.run_id] == "user-42"

    @pytest.mark.asyncio
    async def test_stores_empty_for_non_user_message(self, tracer: AgentRunTracer, topic: AgentInstanceTopic) -> None:
        event = MagicMock(spec=StartEvent)
        event.is_user_message_event = False

        await tracer.trace_run_start(topic, event)

        assert tracer._run_inputs[topic.run_id] == ""
        assert tracer._run_user_ids[topic.run_id] == ""


class TestClearRun:
    """Tests for clear_run — removes cached run metadata."""

    def test_clears_all_caches(self, tracer: AgentRunTracer) -> None:
        run_id = "run-123"
        tracer._run_inputs[run_id] = "input"
        tracer._run_user_ids[run_id] = "user"
        tracer._run_outputs[run_id] = "output"

        tracer.clear_run(run_id)

        assert run_id not in tracer._run_inputs
        assert run_id not in tracer._run_user_ids
        assert run_id not in tracer._run_outputs

    def test_clear_nonexistent_run_is_safe(self, tracer: AgentRunTracer) -> None:
        """clear_run should not raise for an unknown run_id."""
        tracer.clear_run("nonexistent-run")


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
        tracer._run_inputs[topic.run_id] = "user question"
        tracer._run_user_ids[topic.run_id] = "user-42"

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
        tracer._run_inputs[topic.run_id] = ""
        tracer._run_user_ids[topic.run_id] = ""
        tracer._run_outputs[topic.run_id] = "final answer"

        mock_span = MagicMock()
        stop_event = MagicMock()
        stop_event.is_stop_event = True
        stop_event.is_semantic_event = False
        stop_event.to_trace_dict.return_value = {"type": "stop"}

        await tracer.trace_step_stop(mock_span, [stop_event], topic)

        attrs = mock_span.set_attributes.call_args_list[-1][0][0]
        assert attrs["langfuse.trace.output"] == "final answer"


class TestTraceStepError:
    """Tests for trace_step_error — marks span as errored."""

    def test_sets_error_status(self, tracer: AgentRunTracer) -> None:
        mock_span = MagicMock()
        error = RuntimeError("something broke")

        tracer.trace_step_error(mock_span, error)

        mock_span.set_status.assert_called_once_with(StatusCode.ERROR, "something broke")
