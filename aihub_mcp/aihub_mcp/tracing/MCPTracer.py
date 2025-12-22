"""OpenTelemetry tracing instrumentation for MCP requests."""

import logging
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import SpanKind, Status, StatusCode

logger = logging.getLogger(__name__)


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

    def start_tool_span(
        self,
        tool_name: str,
        agent_class: str,
        attributes: dict[str, Any] | None = None,
    ) -> Any:
        """Start a span for tool invocation."""
        if not self._enabled:
            return None

        span_attributes = {
            "mcp.tool.name": tool_name,
            "mcp.agent.class": agent_class,
            "mcp.operation": "tool_invocation",
        }
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
