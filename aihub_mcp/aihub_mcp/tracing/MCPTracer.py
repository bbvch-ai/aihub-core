import logging
from contextvars import ContextVar
from typing import Any

from opentelemetry import trace
from opentelemetry.trace import Span, SpanKind, Status, StatusCode

logger = logging.getLogger(__name__)

# Context variables for thread/run tracking across async boundaries
current_thread_id: ContextVar[str | None] = ContextVar("current_thread_id", default=None)
current_run_id: ContextVar[str | None] = ContextVar("current_run_id", default=None)

# MCP-specific span attribute keys
MCP_THREAD_ID = "mcp.thread_id"
MCP_RUN_ID = "mcp.run_id"
MCP_DISPLAY_ID = "mcp.display_id"
MCP_AGENT_ID = "mcp.agent_id"
MCP_USER_ID = "mcp.user_id"
MCP_TOOL_NAME = "mcp.tool.name"
MCP_AGENT_CLASS = "mcp.agent.class"
MCP_OPERATION = "mcp.operation"
MCP_ELICITATION_TYPE = "mcp.elicitation.type"
MCP_ELICITATION_QUESTION = "mcp.elicitation.question"
MCP_SAMPLING_MESSAGE_COUNT = "mcp.sampling.message_count"
MCP_DISCOVERY_OPERATION = "mcp.discovery.operation"
MCP_DISCOVERY_CALL_ID = "mcp.discovery.call_id"


class MCPTracer:
    """OpenTelemetry tracing for MCP server operations."""

    TRACER_NAME = "aihub_mcp"

    def __init__(self) -> None:
        self._tracer = self._setup_tracer()

    def _setup_tracer(self) -> trace.Tracer:
        """Configure OpenTelemetry tracer using shared lib instrumentor."""
        from aihub_lib.infrastructure.opentelemetry.AihubInstrumentor import AihubInstrumentor
        from aihub_lib.infrastructure.opentelemetry.OpenTelemetrySettings import OpenTelemetrySettings

        settings = OpenTelemetrySettings()
        if settings.ENABLED:
            AihubInstrumentor().instrument()
            logger.info(f"OpenTelemetry tracing enabled: endpoint={settings.EXPORTER_OTLP_ENDPOINT}")
        else:
            logger.info("OpenTelemetry tracing disabled (OTEL_ENABLED=False)")

        return trace.get_tracer(self.TRACER_NAME)

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
    ) -> Span:
        """Start a span for agent execution with full SAAP context."""
        current_thread_id.set(thread_id)
        current_run_id.set(run_id)

        span_attributes: dict[str, Any] = {
            MCP_THREAD_ID: thread_id,
            MCP_RUN_ID: run_id,
            MCP_DISPLAY_ID: display_id,
            MCP_AGENT_ID: agent_id,
            MCP_TOOL_NAME: tool_name,
            MCP_AGENT_CLASS: agent_class,
            MCP_OPERATION: "agent_execution",
        }

        if user_id:
            span_attributes[MCP_USER_ID] = user_id

        if attributes:
            span_attributes.update(attributes)

        return self._tracer.start_span(
            name=f"mcp.agent.{agent_class}",
            kind=SpanKind.SERVER,
            attributes=span_attributes,
        )

    def start_tool_span(
        self,
        tool_name: str,
        agent_class: str,
        attributes: dict[str, Any] | None = None,
    ) -> Span:
        """Start a span for tool invocation."""
        span_attributes: dict[str, Any] = {
            MCP_TOOL_NAME: tool_name,
            MCP_AGENT_CLASS: agent_class,
            MCP_OPERATION: "tool_invocation",
        }

        thread_id = current_thread_id.get()
        run_id = current_run_id.get()
        if thread_id:
            span_attributes[MCP_THREAD_ID] = thread_id
        if run_id:
            span_attributes[MCP_RUN_ID] = run_id

        if attributes:
            span_attributes.update(attributes)

        return self._tracer.start_span(
            name=f"mcp.tool.{tool_name}",
            kind=SpanKind.SERVER,
            attributes=span_attributes,
        )

    def start_elicitation_span(self, hitl_type: str, question: str) -> Span:
        """Start a span for elicitation request."""
        return self._tracer.start_span(
            name=f"mcp.elicitation.{hitl_type}",
            kind=SpanKind.CLIENT,
            attributes={
                MCP_ELICITATION_TYPE: hitl_type,
                MCP_ELICITATION_QUESTION: question[:100],
                MCP_OPERATION: "elicitation",
            },
        )

    def start_sampling_span(self, message_count: int) -> Span:
        """Start a span for sampling request."""
        return self._tracer.start_span(
            name="mcp.sampling",
            kind=SpanKind.CLIENT,
            attributes={
                MCP_SAMPLING_MESSAGE_COUNT: message_count,
                MCP_OPERATION: "sampling",
            },
        )

    def start_discovery_span(self, operation: str, call_id: str | None = None) -> Span:
        """Start a span for agent discovery operations."""
        attributes: dict[str, Any] = {
            MCP_OPERATION: "discovery",
            MCP_DISCOVERY_OPERATION: operation,
        }
        if call_id:
            attributes[MCP_DISCOVERY_CALL_ID] = call_id

        return self._tracer.start_span(
            name=f"mcp.discovery.{operation}",
            kind=SpanKind.INTERNAL,
            attributes=attributes,
        )

    def start_agent_registration_span(self, agent_class: str) -> Span:
        """Start a span for agent registration."""
        return self._tracer.start_span(
            name=f"mcp.discovery.register.{agent_class}",
            kind=SpanKind.INTERNAL,
            attributes={
                MCP_OPERATION: "discovery",
                MCP_DISCOVERY_OPERATION: "register",
                MCP_AGENT_CLASS: agent_class,
            },
        )

    def end_span(
        self,
        span: Span,
        success: bool = True,
        error_message: str | None = None,
    ) -> None:
        """End a span with status."""
        if success:
            span.set_status(Status(StatusCode.OK))
        else:
            span.set_status(Status(StatusCode.ERROR, error_message or "Unknown error"))
            if error_message:
                span.set_attribute("error.message", error_message)

        span.end()

    def add_event(
        self,
        span: Span,
        name: str,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """Add an event to a span."""
        span.add_event(name, attributes=attributes)
