from typing import ClassVar, Self

from swiss_ai_hub.core.tracing.nats_trace_context_propagator import NATSTraceContextPropagator


class NATSMessageHeaders:
    """Helper class for working with NATS message headers in a type-safe way."""

    # Prefix used to mark headers that originate from the external request boundary (API, bot, etc.)
    # and must be forwarded along the agent pipeline so downstream MCP tools can act on behalf of
    # the originating user. Matching is case-insensitive; canonical form is the value below.
    AIHUB_HEADER_PREFIX: ClassVar[str] = "X-AIHub-"

    def __init__(self, headers: dict[str, str] | None = None):
        self.headers = headers or {}

    def with_trace_context(self) -> Self:
        """Add current trace context to headers."""
        self.headers = NATSTraceContextPropagator.inject_trace_context(self.headers)
        return self

    def with_header(self, key: str, value: str) -> Self:
        """Add a custom header."""
        self.headers[key] = value
        return self

    def with_aihub_headers(self, aihub_headers: dict[str, str] | None) -> Self:
        """
        Merge X-AIHub-* request headers into the outgoing NATS headers so they propagate to the
        agent. Tokens and identity carried this way must never be written to persistent stores.
        """
        if not aihub_headers:
            return self
        for key, value in aihub_headers.items():
            self.headers[key] = value
        return self

    def to_dict(self) -> dict[str, str]:
        """Get headers as dictionary."""
        return self.headers

    @classmethod
    def extract_aihub_headers(cls, headers: dict[str, str] | None) -> dict[str, str]:
        """
        Pick out the X-AIHub-* entries from a NATS headers dict, preserving their original case.
        Empty/None input yields an empty dict so callers can unconditionally pass it forward.
        """
        if not headers:
            return {}
        prefix_lower = cls.AIHUB_HEADER_PREFIX.lower()
        return {key: value for key, value in headers.items() if key.lower().startswith(prefix_lower)}
