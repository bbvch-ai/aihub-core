import functools
import inspect
from typing import Any, Callable

from openinference.semconv.trace import SpanAttributes, OpenInferenceMimeTypeValues
from opentelemetry import trace
import json


def tracing() -> Callable:
    """
    A decorator that creates an OpenTelemetry span to trace function inputs and outputs.
    Can be used with both synchronous and asynchronous functions.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = trace.get_tracer(__name__)

            # Create span name from function name
            span_name = f"{func.__module__}.{func.__name__}"

            with tracer.start_as_current_span(span_name) as span:
                try:
                    # Record input parameters
                    input_params = {
                        "args": args,
                        "kwargs": kwargs
                    }
                    span.set_attributes({
                        SpanAttributes.INPUT_VALUE: json.dumps(input_params, default=str),
                        SpanAttributes.INPUT_MIME_TYPE: OpenInferenceMimeTypeValues.JSON.value,
                    })

                    # Execute the async function
                    result = await func(*args, **kwargs)

                    # Record the output
                    span.set_attributes({
                        SpanAttributes.OUTPUT_VALUE: json.dumps(input_params, default=str),
                        SpanAttributes.OUTPUT_MIME_TYPE: OpenInferenceMimeTypeValues.JSON.value,
                    })
                    return result

                except Exception as e:
                    # Record error if any
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = trace.get_tracer(__name__)

            # Create span name from function name
            span_name = f"{func.__module__}.{func.__name__}"

            with tracer.start_as_current_span(span_name) as span:
                try:
                    # Record input parameters
                    input_params = {
                        "args": args,
                        "kwargs": kwargs
                    }
                    span.set_attributes({
                        SpanAttributes.INPUT_VALUE: json.dumps(input_params, default=str),
                        SpanAttributes.INPUT_MIME_TYPE: OpenInferenceMimeTypeValues.JSON.value,
                    })
                    # Execute the function
                    result = func(*args, **kwargs)

                    # Record the output
                    span.set_attributes({
                        SpanAttributes.OUTPUT_VALUE: json.dumps(input_params, default=str),
                        SpanAttributes.OUTPUT_MIME_TYPE: OpenInferenceMimeTypeValues.JSON.value,
                    })
                    return result

                except Exception as e:
                    # Record error if any
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise

        # Check if the function is async or not
        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper

    return decorator
