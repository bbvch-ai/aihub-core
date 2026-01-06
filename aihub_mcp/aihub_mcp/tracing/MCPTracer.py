import logging
from contextvars import ContextVar
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Span, SpanKind, Status, StatusCode

logger = logging.getLogger(__name__)

# Context variables for thread/run tracking across async boundaries
current_thread_id: ContextVar[str | None] = ContextVar("current_thread_id", default=None)
current_run_id: ContextVar[str | None] = ContextVar("current_run_id", default=None)

# OpenInference semantic convention attribute names (for Phoenix integration)
OPENINFERENCE_SESSION_ID = "session.id"
OPENINFERENCE_USER_ID = "user.id"
OPENINFERENCE_SPAN_KIND = "openinference.span.kind"

# MCP-specific attributes
MCP_THREAD_ID = "mcp.thread_id"
MCP_RUN_ID = "mcp.run_id"
MCP_DISPLAY_ID = "mcp.display_id"
MCP_AGENT_ID = "mcp.agent_id"
MCP_TOOL_NAME = "mcp.tool.name"
MCP_AGENT_CLASS = "mcp.agent.class"
MCP_OPERATION = "mcp.operation"


class MCPTracer:
    """OpenTelemetry tracing for MCP server operations with Phoenix/OpenInference support."""

    TRACER_NAME = "aihub_mcp"

    def __init__(self, service_name: str = "aihub_mcp") -> None:
        self._service_name = service_name
        self._tracer: trace.Tracer | None = None
        self._setup_tracer()

    def _setup_tracer(self) -> None:
        """Configure OpenTelemetry tracer with OTLP exporter."""
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            from opentelemetry.sdk.resources import Resource

            resource = Resource.create({"service.name": self._service_name})
            provider = TracerProvider(resource=resource)

            try:
                exporter = OTLPSpanExporter()
                provider.add_span_processor(BatchSpanProcessor(exporter))
            except Exception as e:
                logger.warning(f"Could not configure OTLP exporter: {e}")

            trace.set_tracer_provider(provider)
            self._tracer = trace.get_tracer(self.TRACER_NAME)
            logger.info("OpenTelemetry tracing configured")

        except Exception as e:
            logger.warning(f"Could not configure tracing: {e}")

    @property
    def tracer(self) -> trace.Tracer:
        """Get the tracer instance."""
        if self._tracer is None:
            return trace.get_tracer(self.TRACER_NAME)
        return self._tracer

    def start_agent_execution_span(
        self,
        tool_name: str,
        agent_class: str,
        thread_id: str,
        run_id: str,
        display_id: str,
        agent_id: str,
        user_id: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> Span | None:
        """Start a span for agent execution with full SAAP context."""
        current_thread_id.set(thread_id)
        current_run_id.set(run_id)

        span_attributes: dict[str, Any] = {
            OPENINFERENCE_SESSION_ID: thread_id,
            OPENINFERENCE_SPAN_KIND: "CHAIN",
            MCP_THREAD_ID: thread_id,
            MCP_RUN_ID: run_id,
            MCP_DISPLAY_ID: display_id,
            MCP_AGENT_ID: agent_id,
            MCP_TOOL_NAME: tool_name,
            MCP_AGENT_CLASS: agent_class,
            MCP_OPERATION: "agent_execution",
        }

        if user_id:
            span_attributes[OPENINFERENCE_USER_ID] = user_id

        if attributes:
            span_attributes.update(attributes)

        return self.tracer.start_span(
            name=f"mcp.agent.{agent_class}",
            kind=SpanKind.SERVER,
            attributes=span_attributes,
        )

    def start_tool_span(
        self,
        tool_name: str,
        agent_class: str,
        attributes: dict[str, Any] | None = None,
    ) -> Span | None:
        """Start a span for tool invocation."""
        span_attributes: dict[str, Any] = {
            MCP_TOOL_NAME: tool_name,
            MCP_AGENT_CLASS: agent_class,
            MCP_OPERATION: "tool_invocation",
        }

        thread_id = current_thread_id.get()
        run_id = current_run_id.get()
        if thread_id:
            span_attributes[OPENINFERENCE_SESSION_ID] = thread_id
            span_attributes[MCP_THREAD_ID] = thread_id
        if run_id:
            span_attributes[MCP_RUN_ID] = run_id

        if attributes:
            span_attributes.update(attributes)

        return self.tracer.start_span(
            name=f"mcp.tool.{tool_name}",
            kind=SpanKind.SERVER,
            attributes=span_attributes,
        )

    def start_elicitation_span(self, hitl_type: str, question: str) -> Span | None:
        """Start a span for elicitation request."""
        return self.tracer.start_span(
            name=f"mcp.elicitation.{hitl_type}",
            kind=SpanKind.CLIENT,
            attributes={
                "mcp.elicitation.type": hitl_type,
                "mcp.elicitation.question": question[:100],
                MCP_OPERATION: "elicitation",
            },
        )

    def start_sampling_span(self, message_count: int) -> Span | None:
        """Start a span for sampling request."""
        return self.tracer.start_span(
            name="mcp.sampling",
            kind=SpanKind.CLIENT,
            attributes={
                "mcp.sampling.message_count": message_count,
                MCP_OPERATION: "sampling",
            },
        )

    def start_discovery_span(self, operation: str, call_id: str | None = None) -> Span | None:
        """Start a span for agent discovery operations."""
        attributes: dict[str, Any] = {
            MCP_OPERATION: "discovery",
            "mcp.discovery.operation": operation,
        }
        if call_id:
            attributes["mcp.discovery.call_id"] = call_id

        return self.tracer.start_span(
            name=f"mcp.discovery.{operation}",
            kind=SpanKind.INTERNAL,
            attributes=attributes,
        )

    def start_agent_registration_span(self, agent_class: str) -> Span | None:
        """Start a span for agent registration."""
        return self.tracer.start_span(
            name=f"mcp.discovery.register.{agent_class}",
            kind=SpanKind.INTERNAL,
            attributes={
                MCP_OPERATION: "discovery",
                "mcp.discovery.operation": "register",
                MCP_AGENT_CLASS: agent_class,
            },
        )

    def end_span(
        self,
        span: Span | None,
        success: bool = True,
        error_message: str | None = None,
    ) -> None:
        """End a span with status."""
        if span is None:
            return

        if success:
            span.set_status(Status(StatusCode.OK))
        else:
            span.set_status(Status(StatusCode.ERROR, error_message or "Unknown error"))
            if error_message:
                span.set_attribute("error.message", error_message)

        span.end()

    def add_event(
        self,
        span: Span | None,
        name: str,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """Add an event to a span."""
        if span is None:
            return

        span.add_event(name, attributes=attributes)
