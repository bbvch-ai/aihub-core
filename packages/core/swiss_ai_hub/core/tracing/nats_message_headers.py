from typing import Self

from swiss_ai_hub.core.tracing.nats_trace_context_propagator import NATSTraceContextPropagator


class NATSMessageHeaders:
    """Helper class for working with NATS message headers in a type-safe way."""

    def __init__(self, headers: dict[str, str] = None):
        self.headers = headers or {}

    def with_trace_context(self) -> Self:
        """Add current trace context to headers."""
        self.headers = NATSTraceContextPropagator.inject_trace_context(self.headers)
        return self

    def with_header(self, key: str, value: str) -> Self:
        """Add a custom header."""
        self.headers[key] = value
        return self

    def to_dict(self) -> dict[str, str]:
        """Get headers as dictionary."""
        return self.headers
