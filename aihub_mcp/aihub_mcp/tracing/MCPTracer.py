"""OpenTelemetry tracing instrumentation for MCP requests."""

import logging
from contextvars import ContextVar
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import SpanKind, Status, StatusCode

logger = logging.getLogger(__name__)

# Context variables for thread/run tracking across async boundaries
current_thread_id: ContextVar[str | None] = ContextVar("current_thread_id", default=None)
current_run_id: ContextVar[str | None] = ContextVar("current_run_id", default=None)

# OpenInference semantic convention attribute names
OPENINFERENCE_SESSION_ID = "session.id"
OPENINFERENCE_USER_ID = "user.id"
OPENINFERENCE_SPAN_KIND = "openinference.span.kind"

# Additional MCP-specific attributes
MCP_THREAD_ID = "mcp.thread_id"
MCP_RUN_ID = "mcp.run_id"
MCP_DISPLAY_ID = "mcp.display_id"
MCP_AGENT_ID = "mcp.agent_id"


class MCPTracer:
    """
    OpenTelemetry tracing for MCP server operations.

    Instruments:
    - Tool invocations
    - Agent executions
    - HITL/Elicitation requests
    - Sampling requests
    - Progress notifications
    """

    TRACER_NAME = "aihub_mcp"

    def __init__(self, service_name: str = "aihub_mcp", enabled: bool = True) -> None:
        self._enabled = enabled
        self._service_name = service_name
        self._tracer: trace.Tracer | None = None

        if enabled:
            self._setup_tracer()

    def _setup_tracer(self) -> None:
        """Configure OpenTelemetry tracer."""
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            from opentelemetry.sdk.resources import Resource

            # Create resource with service name
            resource = Resource.create({"service.name": self._service_name})

            # Create tracer provider
            provider = TracerProvider(resource=resource)

            # Add OTLP exporter (Phoenix/Jaeger compatible)
            try:
                exporter = OTLPSpanExporter()
                provider.add_span_processor(BatchSpanProcessor(exporter))
            except Exception as e:
                logger.warning(f"Could not configure OTLP exporter: {e}")

            # Set as global provider
            trace.set_tracer_provider(provider)

            # Get tracer
            self._tracer = trace.get_tracer(self.TRACER_NAME)
            logger.info("OpenTelemetry tracing configured")

        except Exception as e:
            logger.warning(f"Could not configure tracing: {e}")
            self._enabled = False

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
    ) -> Any:
        """
        Start a span for agent execution with full context.

        Sets OpenInference attributes for Phoenix integration:
        - session.id: thread_id for grouping related traces
        - user.id: authenticated user identity
        - openinference.span.kind: CHAIN for agent workflows
        """
        if not self._enabled:
            return None

        # Set context variables for child spans
        current_thread_id.set(thread_id)
        current_run_id.set(run_id)

        span_attributes = {
            # OpenInference semantic conventions
            OPENINFERENCE_SESSION_ID: thread_id,
            OPENINFERENCE_SPAN_KIND: "CHAIN",
            # MCP-specific attributes
            MCP_THREAD_ID: thread_id,
            MCP_RUN_ID: run_id,
            MCP_DISPLAY_ID: display_id,
            MCP_AGENT_ID: agent_id,
            # Tool/agent info
            "mcp.tool.name": tool_name,
            "mcp.agent.class": agent_class,
            "mcp.operation": "agent_execution",
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
    ) -> Any:
        """Start a span for tool invocation (legacy, prefer start_agent_execution_span)."""
        if not self._enabled:
            return None

        span_attributes = {
            "mcp.tool.name": tool_name,
            "mcp.agent.class": agent_class,
            "mcp.operation": "tool_invocation",
        }

        # Include thread/run context if available
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

    def start_elicitation_span(
        self,
        hitl_type: str,
        question: str,
    ) -> Any:
        """Start a span for elicitation request."""
        if not self._enabled:
            return None

        return self.tracer.start_span(
            name=f"mcp.elicitation.{hitl_type}",
            kind=SpanKind.CLIENT,
            attributes={
                "mcp.elicitation.type": hitl_type,
                "mcp.elicitation.question": question[:100],
                "mcp.operation": "elicitation",
            },
        )

    def start_sampling_span(
        self,
        message_count: int,
    ) -> Any:
        """Start a span for sampling request."""
        if not self._enabled:
            return None

        return self.tracer.start_span(
            name="mcp.sampling",
            kind=SpanKind.CLIENT,
            attributes={
                "mcp.sampling.message_count": message_count,
                "mcp.operation": "sampling",
            },
        )

    def end_span(
        self,
        span: Any,
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
        span: Any,
        name: str,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """Add an event to a span."""
        if span is None:
            return

        span.add_event(name, attributes=attributes)
