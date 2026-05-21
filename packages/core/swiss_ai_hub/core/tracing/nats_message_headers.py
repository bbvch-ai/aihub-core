from typing import ClassVar, Self

from swiss_ai_hub.core.tracing.nats_trace_context_propagator import NATSTraceContextPropagator


class NATSMessageHeaders:
    """Helper class for working with NATS message headers in a type-safe way."""

    # Headers with this prefix are forwarded along the agent pipeline so downstream tools can act
    # on behalf of the originating user. Matching is case-insensitive.
    #
    # SECURITY: X-AIHub-* headers come straight from the (untrusted) HTTP client — no proxy
    # injects or vouches for them. The prefix filter on both ends only stops unrelated headers
    # (Authorization, Cookie, ...) from leaking onto the envelope; it is NOT an authenticity
    # check. Any consumer reading these values (e.g. an on-behalf-of token) MUST validate them
    # independently and must never treat an X-AIHub-* value as a trusted identity assertion.
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
        Merge ``X-AIHub-*`` headers into the outgoing NATS headers, dropping any non-prefixed key
        so a caller cannot leak ``Authorization``/``Cookie`` onto the envelope.
        """
        if not aihub_headers:
            return self
        prefix_lower = self.AIHUB_HEADER_PREFIX.lower()
        for key, value in aihub_headers.items():
            if key.lower().startswith(prefix_lower):
                self.headers[key] = value
        return self

    def to_dict(self) -> dict[str, str]:
        """Get headers as dictionary."""
        return self.headers

    @classmethod
    def extract_aihub_headers(cls, headers: dict[str, str] | None) -> dict[str, str]:
        """
        Pick out the ``X-AIHub-*`` entries from a headers dict, lowercasing keys so downstream
        consumers read by a single canonical key. The returned values are untrusted client input
        — see the ``AIHUB_HEADER_PREFIX`` security note before relying on them.
        """
        if not headers:
            return {}
        prefix_lower = cls.AIHUB_HEADER_PREFIX.lower()
        return {key.lower(): value for key, value in headers.items() if key.lower().startswith(prefix_lower)}
