"""Context utilities for propagating OpenInference trace state.

When active, @trace_fn decorated functions add openinference.span.kind = CHAIN
to their spans so they pass through the Langfuse filter in the OTEL collector.
This makes helper functions called within agent steps visible in Langfuse as
children of the step span.

The step-parent mechanism allows agent step spans to reference the original
parent span from NATS headers directly, skipping intermediate NATS infrastructure
spans (receive, process) that would otherwise clutter the Langfuse trace.
Uses Python's native contextvars to guarantee propagation across asyncio boundaries.
"""

from contextlib import contextmanager
from contextvars import ContextVar

from opentelemetry import context

_OPENINFERENCE_TRACE_KEY = "openinference_trace_active"
OPENINFERENCE_ACTIVE_HEADER = "X-Openinference-Active"

_step_parent_context: ContextVar[context.Context | None] = ContextVar("step_parent_context", default=None)


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


def set_step_parent(parent: context.Context) -> None:
    """Store the original NATS parent context so step spans can reference it directly."""
    _step_parent_context.set(parent)


def get_step_parent_context() -> context.Context | None:
    """Retrieve the stored parent context for direct step span parenting."""
    return _step_parent_context.get()
