import json
import logging
from contextlib import asynccontextmanager
from typing import Dict, Callable, Any, List, Optional, AsyncIterator

from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
from openinference.semconv.trace import (
    OpenInferenceMimeTypeValues,
    OpenInferenceSpanKindValues,
    SpanAttributes,
)
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.propagate import inject, extract
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.trace import Span, StatusCode, set_tracer_provider
from pydantic import BaseModel

from agents_core.displayers.EventDisplayer import EventDisplayer
from agents_core.tracing.phoenix.PhoenixConfig import PhoenixConfig
from lib_core.nats.context.BaseContext import BaseContext
from lib_core.nats.events import StartEvent, BaseEvent
from lib_core.nats.events.semantic import SemanticEvent
from lib_core.nats.topics.agents.AgentTopic import AgentTopic
from agents_core.workflow.annotations.custom_types.ListOfSize import ListOfSize

logger = logging.getLogger(__name__)


class RunTraceCoordinator:
    def __init__(self):
        endpoint = f"{PhoenixConfig().PHOENIX_ENDPOINT}/v1/traces"
        tracer_provider = TracerProvider()
        set_tracer_provider(tracer_provider)
        tracer_provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(endpoint)))

        LlamaIndexInstrumentor().instrument(tracer_provider=tracer_provider)
        self.tracer = trace.get_tracer(__name__)

    def trace_run_start(self, topic: AgentTopic, event: StartEvent) -> Dict:
        # Start a new run span and save it
        with self.tracer.start_as_current_span(
            name=f"🤖 {topic.agent_class}",
            kind=trace.SpanKind.SERVER,
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.AGENT.value,
                SpanAttributes.SESSION_ID: topic.thread_id,
                SpanAttributes.INPUT_VALUE: event.model_dump_json(),
                SpanAttributes.INPUT_MIME_TYPE: OpenInferenceMimeTypeValues.JSON.value,
                SpanAttributes.TAG_TAGS: [topic.thread_id, topic.display_id, topic.run_id],
            }
        ) as span:
            logger.debug(f"Tracing run start for {topic.agent_class}")
            span_context = trace.set_span_in_context(span)
            telemetry_headers = {}
            inject(telemetry_headers, context=span_context)
            logger.debug(f"Tracing run start for {topic.agent_class} with headers {telemetry_headers}")
            return telemetry_headers

    @asynccontextmanager
    async def trace_step_start(self, telemetry_headers: Dict, topic: AgentTopic, step_method: Callable,
                               kwargs: Dict[str, Any]) -> AsyncIterator[Span]:
        # Extract the parent context
        parent_context = extract(telemetry_headers)
        logger.debug(
            f"Tracing step start for {topic.agent_class}.{step_method.__name__} with headers {telemetry_headers}")

        # Prepare input values for tracing
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
                input_values[name] = arg

        # Use start_as_current_span to create a child span
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

    async def trace_step_stop(self, span: Span, output_events: Optional[List[BaseEvent]]):
        logger.debug(f"Tracing output {output_events}")
        if output_events:
            span.set_attributes({
                SpanAttributes.OUTPUT_VALUE: json.dumps([ev.to_trace_dict() for ev in output_events]),
                SpanAttributes.OUTPUT_MIME_TYPE: OpenInferenceMimeTypeValues.JSON.value,
            })
            if any(isinstance(ev, SemanticEvent) for ev in output_events):
                semantic_event = next(ev for ev in output_events if isinstance(ev, SemanticEvent))
                span.set_attributes(semantic_event.to_semantic_convention())
        span.set_status(StatusCode.OK)
        span.end()

    async def trace_step_error(self, span: Span, error: Exception):
        """Traces an error that occurred during step execution."""
        span.set_status(StatusCode.ERROR, str(error))
        span.end()
