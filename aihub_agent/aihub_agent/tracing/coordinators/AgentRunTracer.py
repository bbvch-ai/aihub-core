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
from nats.aio.client import Client as NATS
from openinference.semconv.trace import OpenInferenceMimeTypeValues, OpenInferenceSpanKindValues, SpanAttributes
from opentelemetry import context, trace
from opentelemetry.propagate import extract, inject
from opentelemetry.trace import Span, StatusCode
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AgentRunTracer:
    """
    Coordinates the tracing of runs and steps using OpenTelemetry.

    This implementation uses a two-span approach for the agent run:
    1.  An initial, short-lived 'AGENT' span is created to act as the parent
        for all nested step spans.
    2.  A final, long-running 'LLM' span is created at the end of the run
        to capture the total duration and final input/output.
    """

    def __init__(
        self,
        nc: Annotated[NATS, "NATS client for messaging."],
    ):
        self.nc = nc
        self.tracer = get_tracer(__name__)

    def trace_run_start(self, topic: AgentInstanceTopic, event: StartEvent) -> tuple[int, dict[str, str]]:
        """
        Creates the initial parent 'AGENT' span for the run.

        This span has a near-zero duration and acts as the root for all
        subsequent step spans, establishing a clear hierarchy.

        Returns:
            A tuple containing the run's start time and the telemetry headers
            pointing to the new AGENT span as the parent.
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
                    "phoenix.is_root": True,
                    SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.AGENT.value,
                    SpanAttributes.INPUT_VALUE: user_input,
                    SpanAttributes.INPUT_MIME_TYPE: OpenInferenceMimeTypeValues.TEXT.value,
                    SpanAttributes.TAG_TAGS: [topic.thread_id, topic.display_id, topic.run_id],
                }
            )
            span.set_status(StatusCode.OK)
            inject(telemetry_headers, context=context.get_current())

        logger.debug(f"Created parent AGENT span with headers: {telemetry_headers}")
        return start_time_ns, telemetry_headers

    def trace_run_completion(
        self,
        start_time_ns: int,
        telemetry_headers: dict[str, str],
        topic: AgentInstanceTopic,
        final_event: StopEvent | ExceptionEvent,
    ):
        """
        Creates the final child span that captures the run's total duration and output.
        """
        parent_context = extract(telemetry_headers)

        with self.tracer.start_as_current_span(
            name=f"Run {topic.run_id}",
            context=parent_context,
            kind=trace.SpanKind.INTERNAL,
            start_time=start_time_ns,
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
        telemetry_headers: dict[str, str],
        topic: AgentInstanceTopic,
        step_method: Callable,
        kwargs: dict[str, Any],
    ) -> AsyncIterator[Span]:
        """
        Starts a step-level span as a child of the main 'AGENT' span.
        """
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

    async def trace_step_stop(self, span: Span, output_events: list[BaseEvent] | None):
        """
        Ends the step span with a success status.
        """
        if output_events:
            span.set_attributes(
                {
                    SpanAttributes.OUTPUT_VALUE: json.dumps([ev.to_trace_dict() for ev in output_events]),
                    SpanAttributes.OUTPUT_MIME_TYPE: OpenInferenceMimeTypeValues.JSON.value,
                }
            )
            semantic_event = next((ev for ev in output_events if ev.is_semantic_event), None)
            if semantic_event:
                span.set_attributes(semantic_event.to_semantic_convention())
        span.set_status(StatusCode.OK)

    async def trace_step_error(self, span: Span, error: Exception):
        """
        Marks the step span as errored and ends it.
        """
        span.set_status(StatusCode.ERROR, str(error))
        span.end()
