"""Context utilities for propagating OpenInference trace state.

When active, @trace_fn decorated functions will add openinference.span.kind = CHAIN
to their spans, allowing them to pass through the Phoenix filter in the OTEL collector.
This bridges the gap between agent step spans and their child OpenInference spans
(embeddings, LLM calls), maintaining the parent-child chain in Phoenix.
"""

from contextlib import contextmanager

from opentelemetry import context

_OPENINFERENCE_TRACE_KEY = "openinference_trace_active"


@contextmanager
def openinference_trace_context():
    """Mark the current execution context as being within an OpenInference trace."""
    ctx = context.set_value(_OPENINFERENCE_TRACE_KEY, True)
    token = context.attach(ctx)
    try:
        yield
    finally:
        context.detach(token)


def is_openinference_trace_active() -> bool:
    """Check if the current execution is within an OpenInference trace."""
    return context.get_value(_OPENINFERENCE_TRACE_KEY) is True
