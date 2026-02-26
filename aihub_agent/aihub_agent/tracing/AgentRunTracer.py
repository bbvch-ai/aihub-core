import json
import logging
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Annotated, Any

from aihub_lib.context.BaseContext import BaseContext
from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.infrastructure.opentelemetry.tracing.openinference_context import (
    openinference_trace_context,
)
from aihub_lib.infrastructure.opentelemetry.tracing.SmartTracer import get_tracer
from aihub_lib.nats.events import BaseEvent, StartEvent
from aihub_lib.nats.topics.agents.AgentInstanceTopic import AgentInstanceTopic
from aihub_lib.nats.workflow.annotations.custom_types.ListOfSize import ListOfSize
from openinference.semconv.trace import OpenInferenceMimeTypeValues, OpenInferenceSpanKindValues, SpanAttributes
from opentelemetry import context, propagate, trace
from opentelemetry.trace import Span, StatusCode, set_span_in_context
from pydantic import BaseModel
from redis.asyncio import Redis

from aihub_agent.context.run.RunContext import RunContext

logger = logging.getLogger(__name__)

_TRACE_INPUT_KEY = "_trace_input"
_TRACE_USER_ID_KEY = "_trace_user_id"
_TRACE_OUTPUT_KEY = "_trace_output"
_TRACE_AITL_PARENT_CONTEXT_KEY = "_trace_aitl_parent_context"
_TRACE_AITL_TARGET_AGENT_CLASS_KEY = "_trace_aitl_target_agent_class"


class AgentRunTracer:
    """
    Coordinates the tracing of runs and steps using OpenTelemetry and Langfuse.

    Each workflow step gets its own span with Langfuse trace-level attributes
    (name, session, user, input/output) set via span attributes. Langfuse
    groups these spans into traces automatically.

    Run metadata (user input, user ID, LLM output) is stored in Redis via
    RunContext for cross-runner access in distributed environments. Cleanup
    is handled by RunContext.delete_all() in the dispatcher on run completion.

    The ``langfuse.*`` span attributes used throughout this class are the
    documented way to enrich standard OTEL spans for Langfuse's OTEL ingestion
    endpoint (see https://langfuse.com/docs/integrations/opentelemetry).
    Regular OTEL tracing still works alongside them — any consumer that does
    not understand these attributes simply ignores them.
    """

    def __init__(self, redis: Annotated[Redis, "Redis client for distributed storage."]):
        self.redis = redis
        self.tracer = get_tracer(__name__)

    def _run_context_for(self, topic: AgentInstanceTopic) -> RunContext:
        """Create a RunContext scoped to the given topic for trace metadata storage."""
        return RunContext.for_topic(self.redis, topic)

    async def trace_run_start(self, topic: AgentInstanceTopic, event: StartEvent):
        """Stores the user input and user ID for the run in Redis for cross-runner access."""
        user_input = event.user_query if event.is_user_message_event else ""
        user_id = event.user.id if event.is_user_message_event else ""
        logger.debug(f"Storing run metadata for {topic.run_id}")

        run_context = self._run_context_for(topic)
        await run_context.set(_TRACE_INPUT_KEY, user_input)
        await run_context.set(_TRACE_USER_ID_KEY, user_id)

    @asynccontextmanager
    async def trace_step_start(
        self,
        topic: AgentInstanceTopic,
        step_method: Callable,
        kwargs: dict[str, Any],
    ) -> AsyncIterator[Span]:
        """
        Starts a step-level span for detailed observability.

        Uses explicit context attachment to ensure span context is properly
        propagated through async operations. This is required because using
        a sync 'with' block inside an async context manager can lose context
        across await boundaries. See: https://github.com/open-telemetry/opentelemetry-python/discussions/3792
        """
        logger.debug(f"Tracing step start for {topic.agent_class}.{step_method.__name__}")

        # Serialize inputs for observability
        input_values = {}
        for name, arg in kwargs.items():
            if isinstance(arg, BaseEvent):
                input_values[name] = arg.to_trace_dict()
            elif isinstance(arg, BaseContext):
                input_values[name] = await arg.to_serializable()
            elif isinstance(arg, ListOfSize):
                input_values[name] = [ev.model_dump() for ev in arg]
            elif isinstance(arg, EventDisplayer):
                pass
            elif isinstance(arg, BaseModel):
                input_values[name] = arg.model_dump()
            else:
                try:
                    json.dumps(arg)
                    input_values[name] = arg
                except TypeError:
                    input_values[name] = str(arg)

        span_name = f"{topic.agent_class}.{step_method.__name__}"
        attributes = {
            SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
            SpanAttributes.SESSION_ID: topic.thread_id,
            SpanAttributes.INPUT_VALUE: json.dumps(input_values),
            SpanAttributes.INPUT_MIME_TYPE: OpenInferenceMimeTypeValues.JSON.value,
            SpanAttributes.TAG_TAGS: [topic.thread_id, topic.display_id, topic.run_id],
        }

        # If this agent was delegated via AITL, re-parent under the wrapper span
        parent_context = await self._get_aitl_parent_context(topic)

        span = self.tracer.start_span(
            name=span_name,
            context=parent_context,
            kind=trace.SpanKind.CONSUMER,
            attributes=attributes,
        )

        # Create a new context with this span as the current span
        # and explicitly attach it so it persists across async boundaries
        ctx = set_span_in_context(span)
        token = context.attach(ctx)

        with openinference_trace_context():
            try:
                yield span
            finally:
                # Always detach the context and end the span
                context.detach(token)
                span.end()
                logger.debug(f"Finished tracing step: {span_name}")

    async def trace_step_stop(self, span: Span, output_events: list[BaseEvent] | None, topic: AgentInstanceTopic):
        """
        Ends the step span with a success status and sets Langfuse trace-level display.
        """
        run_context = self._run_context_for(topic)
        user_input = await run_context.get(_TRACE_INPUT_KEY, "")
        user_id = await run_context.get(_TRACE_USER_ID_KEY, "")

        is_final_step = False
        if output_events:
            is_final_step = any(ev.is_stop_event for ev in output_events)
            span.set_attributes(
                {
                    SpanAttributes.OUTPUT_VALUE: json.dumps([ev.to_trace_dict() for ev in output_events], default=str),
                    SpanAttributes.OUTPUT_MIME_TYPE: OpenInferenceMimeTypeValues.JSON.value,
                }
            )
            semantic_event = next((ev for ev in output_events if ev.is_semantic_event), None)
            if semantic_event:
                await self._set_semantic_attributes(span, semantic_event, topic)

        # AITL-delegated agents must not overwrite the caller's trace-level display
        is_aitl_delegated = await run_context.get(_TRACE_AITL_PARENT_CONTEXT_KEY) is not None

        if is_aitl_delegated:
            trace_attrs: dict[str, Any] = {
                "langfuse.session.id": topic.thread_id,
                "deployment.environment.name": "agent",
            }
        else:
            trace_attrs: dict[str, Any] = {
                "langfuse.trace.name": f"🤖 {topic.agent_class}/{topic.agent_id}",
                "langfuse.trace.input": user_input,
                "langfuse.trace.tags": [topic.agent_class, topic.agent_id],
                "langfuse.trace.metadata.agent_class": topic.agent_class,
                "langfuse.trace.metadata.agent_id": topic.agent_id,
                "langfuse.trace.metadata.run_id": topic.run_id,
                "langfuse.trace.metadata.display_id": topic.display_id,
                "langfuse.user.id": user_id,
                "langfuse.session.id": topic.thread_id,
                "deployment.environment.name": "agent",
            }
            if is_final_step:
                trace_attrs["langfuse.trace.output"] = await run_context.get(_TRACE_OUTPUT_KEY, "")
        span.set_attributes(trace_attrs)

        span.set_status(StatusCode.OK)

    async def _set_semantic_attributes(self, span: Span, semantic_event: BaseEvent, topic: AgentInstanceTopic):
        """Extracts semantic conventions, usage details, and caches LLM output for the trace."""
        span.set_attributes(semantic_event.to_semantic_convention())

        if hasattr(semantic_event, "output_messages") and semantic_event.output_messages:
            output = semantic_event.output_messages[-1].content or ""
            run_context = self._run_context_for(topic)
            await run_context.set(_TRACE_OUTPUT_KEY, output)

        if hasattr(semantic_event, "token_count_prompt") and hasattr(semantic_event, "token_count_completion"):
            usage_details = {
                "input": semantic_event.token_count_prompt or 0,
                "output": semantic_event.token_count_completion or 0,
                "total": semantic_event.token_count_total or 0,
            }
            span.set_attribute("langfuse.observation.usage_details", json.dumps(usage_details))

            if hasattr(semantic_event, "chat_model_name") and semantic_event.chat_model_name:
                span.set_attribute("langfuse.observation.model", semantic_event.chat_model_name)

    async def start_aitl_wrapper_span(
        self,
        caller_topic: AgentInstanceTopic,
        target_agent_class: str,
        target_agent_id: str,
        target_run_id: str,
        target_thread_id: str,
        start_event: StartEvent,
    ) -> Span:
        """Creates a wrapper span bridging the caller's step to the delegated agent's steps.

        The span uses openinference.span.kind=AGENT so it survives the OTEL
        Collector filter and appears in Langfuse. Its trace_id + span_id are
        stored in the target's RunContext so the delegated agent can re-parent
        its step spans under this wrapper.
        """
        input_value = start_event.user_query if start_event.is_user_message_event else ""
        span = self.tracer.start_span(
            name=f"AITL -> {target_agent_class}/{target_agent_id}",
            kind=trace.SpanKind.INTERNAL,
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.AGENT.value,
                SpanAttributes.SESSION_ID: caller_topic.thread_id,
                SpanAttributes.INPUT_VALUE: input_value,
            },
        )

        carrier: dict[str, str] = {}
        ctx = set_span_in_context(span)
        propagate.inject(carrier, context=ctx)

        target_topic = AgentInstanceTopic(
            agent_class=target_agent_class,
            agent_id=target_agent_id,
            thread_id=target_thread_id,
            run_id=target_run_id,
            display_id=caller_topic.display_id,
            event_id=caller_topic.event_id,
            event_type="control_event",
            event_name="StartEvent",
        )
        target_run_context = self._run_context_for(target_topic)
        await target_run_context.set(_TRACE_AITL_PARENT_CONTEXT_KEY, carrier)
        await target_run_context.set(_TRACE_AITL_TARGET_AGENT_CLASS_KEY, target_agent_class)

        return span

    async def end_aitl_wrapper_span(self, span: Span, *, success: bool, target_topic: AgentInstanceTopic):
        """Ends the AITL wrapper span with the delegated agent's cached LLM output."""
        target_run_context = self._run_context_for(target_topic)
        output = await target_run_context.get(_TRACE_OUTPUT_KEY, "")
        if output:
            span.set_attribute(SpanAttributes.OUTPUT_VALUE, output)
        if success:
            span.set_status(StatusCode.OK)
        else:
            span.set_status(StatusCode.ERROR, "Delegated agent failed")
        span.end()

    async def _get_aitl_parent_context(self, topic: AgentInstanceTopic) -> trace.Context | None:
        """Reconstructs the AITL wrapper span as parent context for re-parenting.

        Uses the standard W3C TraceContext propagator to deserialize the parent
        span context from the carrier stored in Redis.

        Returns None for non-AITL agents (default OTEL context is used).
        Checks agent_class to handle the share_run_id=True edge case where
        both agents share a RunContext.
        """
        run_context = self._run_context_for(topic)
        carrier = await run_context.get(_TRACE_AITL_PARENT_CONTEXT_KEY)
        if carrier is None:
            return None

        target_class = await run_context.get(_TRACE_AITL_TARGET_AGENT_CLASS_KEY)
        if target_class != topic.agent_class:
            return None

        return propagate.extract(carrier)

    def trace_step_error(self, span: Span, error: Exception):
        """Marks the step span as errored. The span is ended by the context manager."""
        span.set_status(StatusCode.ERROR, str(error))
