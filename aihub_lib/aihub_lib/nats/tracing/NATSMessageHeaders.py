from typing import Self

from aihub_lib.infrastructure.opentelemetry.tracing.openinference_context import (
    OPENINFERENCE_ACTIVE_HEADER,
    is_openinference_trace_active,
)
from aihub_lib.nats.tracing.NATSTraceContextPropagator import NATSTraceContextPropagator


class NATSMessageHeaders:
    """Helper class for working with NATS message headers in a type-safe way."""

    def __init__(self, headers: dict[str, str] = None):
        self.headers = headers or {}

    def with_trace_context(self) -> Self:
        """Add current trace context and OpenInference state to headers."""
        self.headers = NATSTraceContextPropagator.inject_trace_context(self.headers)
        if is_openinference_trace_active():
            self.headers[OPENINFERENCE_ACTIVE_HEADER] = "true"
        return self

    def with_header(self, key: str, value: str) -> Self:
        """Add a custom header."""
        self.headers[key] = value
        return self

    def to_dict(self) -> dict[str, str]:
        """Get headers as dictionary."""
        return self.headers
