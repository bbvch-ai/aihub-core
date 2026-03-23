import asyncio
import functools

from opentelemetry.instrumentation.utils import suppress_instrumentation


def no_trace(func):
    """Suppress all tracing for this function and its sub-calls."""
    if asyncio.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with suppress_instrumentation():
                return await func(*args, **kwargs)

        return async_wrapper
    else:

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with suppress_instrumentation():
                return func(*args, **kwargs)

        return sync_wrapper
