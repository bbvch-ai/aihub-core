import asyncio
import json
import logging
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Annotated, Any

from aihub_lib.context.BaseContext import BaseContext
from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.infrastructure.phoenix.PhoenixSettings import PhoenixSettings
from aihub_lib.nats.events import BaseEvent, ExceptionEvent, StartEvent, StopEvent
from aihub_lib.nats.subscribers.agent.AgentNCSubscriber import AgentNCSubscriber
from aihub_lib.nats.topic_managers.agents.AgentThreadTopicManager import AgentThreadTopicManager
from aihub_lib.nats.topics.agents.AgentInstanceTopic import AgentInstanceTopic
from aihub_lib.nats.workflow.annotations.custom_types.ListOfSize import ListOfSize
from nats.aio.client import Client as NATS
from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
from openinference.semconv.resource import ResourceAttributes
from openinference.semconv.trace import OpenInferenceMimeTypeValues, OpenInferenceSpanKindValues, SpanAttributes
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.propagate import extract, inject
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Span, StatusCode, set_tracer_provider
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class RunTraceCoordinator:
    """
    Coordinates the tracing of runs and steps using OpenTelemetry. It integrates with NATS and JetStream-based
    systems, starting and stopping spans corresponding to entire runs and individual workflow steps.

    Observability is critical in complex, distributed AI workflows. The RunTraceCoordinator:
    - Starts a run-level trace on `StartEvent`.
    - Waits for a `StopEvent` or `ExceptionEvent` to conclude the run.
    - Instruments steps so their inputs/outputs are captured as child spans.
    This improves debugging, performance monitoring, and auditing by providing rich telemetry through OpenTelemetry.

    ### Key Features
    - **Run-Level Traces:**
      On `StartEvent`, creates a server-span representing the whole run. Gathers user input and tags the span.
      On `StopEvent` or `ExceptionEvent`, it concludes the run’s span.
    - **Step-Level Traces:**
      Provides `trace_step_start` / `trace_step_stop` / `trace_step_error` context managers and methods to
      encapsulate each step execution in its own span.
    - **Integration with Phoenix:**
      Sends telemetry to a Phoenix endpoint for centralized observability. Attaches user input/output and
      semantic conventions to spans.

    ### Lifecycle
    1. **Run Start:** `trace_run_start` is called when a run begins. It creates a server span and returns
       telemetry headers that can be injected into subsequent steps for consistent correlation.
    2. **Run Termination:** On `StopEvent` or `ExceptionEvent`, `trace_run_stop` updates
        the run span status and ends it.
    3. **Step Execution:** `trace_step_start` creates a child span of the run’s span. Steps’ inputs/outputs
       are recorded. On success, `trace_step_stop` is called. On error, `trace_step_error` is invoked.

    ### Example
    A run might start with a `StartEvent`, triggering `trace_run_start`. Steps executed during the run will
    each get their own spans, linked back to the run’s parent span. When a `StopEvent` arrives, `trace_run_stop`
    finalizes the run’s trace, ensuring all spans are ended properly.
    """

    def __init__(
        self,
        nc: Annotated[NATS, "NATS client for messaging."],
        project_name: Annotated[str, "Name that shows up as project in phoenix."],
    ):
        self.nc = nc

        endpoint = f"{PhoenixSettings().ENDPOINT}/v1/traces"
        auth_token = PhoenixSettings().AUTH_TOKEN.get_secret_value()
        headers = {"authorization": f"Bearer {auth_token}"} if auth_token else {}
        tracer_provider = TracerProvider(resource=Resource({ResourceAttributes.PROJECT_NAME: project_name}))
        set_tracer_provider(tracer_provider)
        tracer_provider.add_span_processor(
            BatchSpanProcessor(
                OTLPSpanExporter(endpoint, headers=headers),
                max_queue_size=1024 * 512,
                max_export_batch_size=1024 * 512,
                schedule_delay_millis=30_000,
            )
        )

        LlamaIndexInstrumentor().instrument(tracer_provider=tracer_provider)
        self.tracer = trace.get_tracer(__name__)
        self._background_tasks: set[asyncio.Task] = set()

    def trace_run_start(self, topic: AgentInstanceTopic, event: StartEvent) -> dict[str, str]:
        """
        Initiates a run-level span upon receiving a StartEvent.

        - Extracts user input (if any) from the `StartEvent`.
        - Creates a server span tagged with the agent class, run/thread identifiers, and initial input.
        - Injects telemetry headers for correlation, used by subsequent steps.

        Returns a dict of telemetry headers to pass along for consistent parent-child relationships in spans.
        """
        user_input = event.user_query if event.is_user_message_event else ""
        with self.tracer.start_as_current_span(
            name=f"🤖 {topic.agent_class}",
            kind=trace.SpanKind.SERVER,
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.LLM.value,
                SpanAttributes.INPUT_VALUE: user_input,
                SpanAttributes.INPUT_MIME_TYPE: OpenInferenceMimeTypeValues.TEXT.value,
                SpanAttributes.TAG_TAGS: [
                    topic.thread_id,
                    topic.display_id,
                    topic.run_id,
                ],
            },
            end_on_exit=False,
        ) as span:
            logger.debug(f"Tracing run start for {topic.agent_class}")
            span_context = trace.set_span_in_context(span)
            telemetry_headers: dict[str, str] = {}
            inject(telemetry_headers, context=span_context)
            logger.debug(f"Tracing run start for {topic.agent_class} with headers {telemetry_headers}")
            task = asyncio.create_task(self._end_span_on_event(topic, span))
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)
            return telemetry_headers

    async def _end_span_on_event(self, topic: AgentInstanceTopic, span: Span):
        """
        Waits for a StopEvent or ExceptionEvent to conclude the run’s span, meanwhile accumulating output
        (like chunks) from events that arrive during the run.
        """
        response_aggregate = ""

        async def handler(event: BaseEvent, t: AgentInstanceTopic):
            nonlocal response_aggregate
            if event.is_chunk_event:
                logger.debug("Received ChunkEvent in tracing coordinator")
                response_aggregate += event.content
            if event.is_stop_event or event.is_exception_event:
                logger.debug("Received StopEvent/ExceptionEvent in tracing coordinator")
                self.trace_run_stop(span, event, content=response_aggregate)
                await subscriber.stop()

        subscriber = AgentNCSubscriber.for_all_thread_events(
            nc=self.nc,
            topic_manager=AgentThreadTopicManager.from_agent_topic(topic),
            handler=handler,
        )
        logger.debug(f"Starting subscriber for {topic.agent_class}")
        await subscriber.start()

    def trace_run_stop(self, span: Span, event: StopEvent | ExceptionEvent, content: str):
        """
        Ends the run-level span. If it’s an ExceptionEvent, sets the span status to ERROR.
        Otherwise, sets status OK and adds output content as a traced attribute.
        """
        logger.debug("Stopping span due to StopEvent/ExceptionEvent")

        if event.is_exception_event:
            span.set_status(StatusCode.ERROR, event.message)
        else:
            span.set_status(StatusCode.OK)

        span.set_attributes(
            {
                SpanAttributes.OUTPUT_VALUE: content,
                SpanAttributes.OUTPUT_MIME_TYPE: OpenInferenceMimeTypeValues.TEXT.value,
            }
        )
        span.end()

    @asynccontextmanager
    async def trace_step_start(
        self,
        telemetry_headers: dict[str, str],
        topic: AgentInstanceTopic,
        step_method: Callable,
        kwargs: dict[str, Any],
    ) -> AsyncIterator[Span]:
        """
        Context manager that starts a step-level child span. It:
        - Extracts the parent context from telemetry_headers.
        - Records the step input as JSON.
        - Yields a span that the caller must eventually stop or error-out.

        On exit, the caller is expected to call `trace_step_stop` or `trace_step_error`.
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
                input_values[name] = [ev.model_dump() for ev in arg]  # each event serialized
            elif isinstance(arg, EventDisplayer):
                # Displayers are side-effects, no serialization needed
                pass
            elif isinstance(arg, BaseModel):
                input_values[name] = arg.model_dump()
            else:
                # Attempt JSON serialization, fallback to str
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
        Ends the step span. If `output_events` are present, serializes them and attaches to the span.
        If there's a `SemanticEvent`, sets semantic conventions too.
        """
        logger.debug(f"Tracing output {output_events}")
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
        Marks the step span as errored and ends it. This should be called
        when a step raises an exception.
        """
        span.set_status(StatusCode.ERROR, str(error))
        span.end()
