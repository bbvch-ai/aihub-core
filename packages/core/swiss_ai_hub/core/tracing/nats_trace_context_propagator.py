import logging

from opentelemetry import context, propagate, trace

from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.smart_tracer import get_tracer

logger = logging.getLogger(__name__)


class NATSTraceContextPropagator:
    """
    Utility class for propagating OpenTelemetry trace context through NATS messages.

    This enables distributed tracing across microservices communicating via NATS
    by injecting trace context into message headers on publish and extracting
    it on subscribe.
    """

    @staticmethod
    def inject_trace_context(headers: dict[str, str] = None) -> dict[str, str]:
        """
        Inject the current OpenTelemetry trace context into NATS message headers.
        """
        if headers is None:
            headers = {}

        current_context = context.get_current()
        propagate.inject(headers, context=current_context)

        logger.debug(f"Injected trace context into headers: {headers}")
        return headers

    @staticmethod
    def extract_and_activate_trace_context(headers: dict[str, str]) -> context.Context:
        """
        Extract trace context from NATS message headers and activate it.
        """
        if not headers:
            logger.debug("No headers provided, using current context")
            return context.get_current()

        extracted_context = propagate.extract(headers)

        if extracted_context == context.get_current():
            logger.debug("No trace context found in headers")
            return extracted_context

        context.attach(extracted_context)
        logger.debug(f"Activated trace context from headers: {headers}")

        return extracted_context

    @staticmethod
    def create_child_span(span_name: str, headers: dict[str, str] = None) -> trace.Span:
        """
        Create a child span from trace context in headers.
        """
        parent_context = propagate.extract(headers or {})

        tracer = get_tracer(__name__)
        span = tracer.start_span(span_name, context=parent_context)

        logger.debug(f"Created child span '{span_name}' from extracted context")
        return span
