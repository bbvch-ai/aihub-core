"""Context utilities for propagating OpenInference trace state.
When active, @trace_fn decorated functions and NATS infrastructure spans will add
openinference.span.kind = CHAIN to their spans, allowing them to pass through
the Phoenix filter in the OTEL collector. This maintains the parent-child chain
in Phoenix across agent steps, function calls, and agent-in-the-loop boundaries.
"""

from contextlib import contextmanager

from opentelemetry import context

_OPENINFERENCE_TRACE_KEY = "openinference_trace_active"
OPENINFERENCE_ACTIVE_HEADER = "X-Openinference-Active"


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


def set_openinference_active_in_context(ctx: context.Context) -> context.Context:
    """Return a new context with the OpenInference trace flag set."""
    return context.set_value(_OPENINFERENCE_TRACE_KEY, True, ctx)
