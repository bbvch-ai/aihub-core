import json
import logging
import time
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Annotated, Any

from aihub_lib.context.BaseContext import BaseContext
from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.infrastructure.opentelemetry.tracing.SmartTracer import get_tracer
from aihub_lib.nats.events import BaseEvent, ExceptionEvent, StartEvent, StopEvent
from aihub_lib.nats.topics.agents.AgentInstanceTopic import AgentInstanceTopic
from aihub_lib.nats.workflow.annotations.custom_types.ListOfSize import ListOfSize
from cachetools import TTLCache
from openinference.semconv.trace import OpenInferenceMimeTypeValues, OpenInferenceSpanKindValues, SpanAttributes
from opentelemetry import context, trace
from opentelemetry.propagate import extract, inject
from opentelemetry.trace import Span, StatusCode
from pydantic import BaseModel
from redis.asyncio import Redis

from aihub_agent.context.run.RunContext import RunContext

logger = logging.getLogger(__name__)


class AgentRunTracer:
    """
    Coordinates the tracing of runs and steps using OpenTelemetry.

    This implementation uses a two-span approach for the agent run:
    1.  An initial, short-lived 'AGENT' span is created to act as the parent
        for all nested step spans.
    2.  A final, long-running 'CHAIN' span is created at the end of the run
        to capture the total duration and final input/output.
    """

    _telemetry_headers = "__telemetry_headers__"
    _run_start_time_ns = "__run_start_time_ns__"
    _telemetry_header_cache = TTLCache(maxsize=10_000, ttl=300)

    def __init__(
        self,
        redis: Annotated[Redis, "Redis client for distributed storage."],
    ):
        self.redis = redis
        self.tracer = get_tracer(__name__)

    async def trace_run_start(self, topic: AgentInstanceTopic, event: StartEvent):
        """
        Creates the initial parent 'AGENT' span for the run.

        This span has a near-zero duration and acts as the root for all
        subsequent step spans, establishing a clear hierarchy.
        """
        start_time_ns = time.time_ns()
        user_input = event.user_query if event.is_user_message_event else ""
        telemetry_headers: dict[str, str] = {}

        with self.tracer.start_as_current_span(
            name=f"🤖 {topic.agent_class}",
            kind=trace.SpanKind.INTERNAL,
        ) as span:
            span.set_attributes(
                {
                    SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.AGENT.value,
                    SpanAttributes.INPUT_VALUE: user_input,
                    SpanAttributes.INPUT_MIME_TYPE: OpenInferenceMimeTypeValues.TEXT.value,
                    SpanAttributes.TAG_TAGS: [topic.thread_id, topic.display_id, topic.run_id],
                }
            )
            span.set_status(StatusCode.OK)
            inject(telemetry_headers, context=context.get_current())

        logger.debug(f"Created parent AGENT span with headers: {telemetry_headers}")

        run_context = RunContext.for_topic(self.redis, topic)
        await run_context.set(self._run_start_time_ns, start_time_ns)
        await run_context.set(self._telemetry_headers, telemetry_headers)

    async def trace_run_completion(
        self,
        topic: AgentInstanceTopic,
        final_event: StopEvent | ExceptionEvent,
    ):
        """
        Creates the final child span that captures the run's total duration and output.
        """
        run_context = RunContext.for_topic(self.redis, topic)

        start_time = await run_context.get(self._run_start_time_ns)
        telemetry_headers = await run_context.get(self._telemetry_headers)

        parent_context = extract(telemetry_headers)

        with self.tracer.start_as_current_span(
            name=f"Run {topic.run_id}",
            context=parent_context,
            kind=trace.SpanKind.INTERNAL,
            start_time=start_time,
        ) as span:
            span.set_attributes(
                {
                    SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
                    SpanAttributes.TAG_TAGS: [topic.thread_id, topic.display_id, topic.run_id],
                }
            )

            if final_event.is_exception_event:
                span.set_status(StatusCode.ERROR, final_event.message)
            else:
                span.set_status(StatusCode.OK)

            logger.debug(f"Exporting final run completion span for {topic.run_id}.")

    @asynccontextmanager
    async def trace_step_start(
        self,
        topic: AgentInstanceTopic,
        step_method: Callable,
        kwargs: dict[str, Any],
    ) -> AsyncIterator[Span]:
        """
        Starts a step-level span as a child of the main 'AGENT' span.
        """
        run_context = RunContext.for_topic(self.redis, topic)

        if topic.run_id not in self._telemetry_header_cache:
            telemetry_headers = await run_context.get(self._telemetry_headers)
            self._telemetry_header_cache[topic.run_id] = telemetry_headers
        else:
            telemetry_headers = self._telemetry_header_cache[topic.run_id]

        parent_context = extract(telemetry_headers)
        logger.debug(
            f"Tracing step start for {topic.agent_class}.{step_method.__name__} with headers {telemetry_headers}"
        )

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

        with self.tracer.start_as_current_span(
            name=span_name,
            kind=trace.SpanKind.CONSUMER,
            context=parent_context,
            attributes=attributes,
        ) as span:
            try:
                yield span
            finally:
                logger.debug(f"Finished tracing step: {span_name}")

    def trace_step_stop(self, span: Span, output_events: list[BaseEvent] | None):
        """
        Ends the step span with a success status.
        """
        if output_events:
            span.set_attributes(
                {
                    SpanAttributes.OUTPUT_VALUE: json.dumps([ev.to_trace_dict() for ev in output_events], default=str),
                    SpanAttributes.OUTPUT_MIME_TYPE: OpenInferenceMimeTypeValues.JSON.value,
                }
            )
            semantic_event = next((ev for ev in output_events if ev.is_semantic_event), None)
            if semantic_event:
                span.set_attributes(semantic_event.to_semantic_convention())
        span.set_status(StatusCode.OK)

    def trace_step_error(self, span: Span, error: Exception):
        """
        Marks the step span as errored and ends it.
        """
        span.set_status(StatusCode.ERROR, str(error))
        span.end()
