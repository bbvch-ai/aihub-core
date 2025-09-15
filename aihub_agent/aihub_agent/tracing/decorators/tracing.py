import inspect
import json
from collections.abc import Callable
from typing import Any

from aihub_lib.infrastructure.opentelemetry.tracing.SmartTracer import get_tracer
from openinference.semconv.trace import OpenInferenceMimeTypeValues, SpanAttributes
from opentelemetry.trace import StatusCode


def tracing() -> Callable:
    """
    Decorator that creates an OpenTelemetry span to trace a function’s inputs and outputs.

    ### Why This Decorator?
    Tracing functions (both sync and async) provides visibility into execution time, inputs,
    and outputs. This is especially useful in complex AI workflows where understanding the
    flow of data is crucial for debugging and optimizing performance.

    ### Features
    - Supports synchronous and asynchronous functions.
    - Captures arguments and return values as JSON, attaching them to the span for observability.
    - Marks the span as errored if an exception is raised, aiding error tracking and alerting.

    ### How It Works
    1. On invocation, starts a span named after the function’s module and name.
    2. Serializes and records `args` and `kwargs` as the input.
    3. Executes the function:
       - For async: awaits the function.
       - For sync: runs it directly.
    4. On success, records the output (return value) in the span.
    5. On failure, records the exception in the span and sets the span’s status to ERROR.

    ### Example
    ```python
    @tracing()
    def my_function(x, y):
        return x + y

    # This call is traced, with inputs (x, y) and output recorded.
    my_function(2, 3)
    ```

    ### Notes
    - If a return value is not JSON-serializable, it is converted to a string.
    - The default `OUTPUT_VALUE` was corrected to record the actual result instead of reusing input_params.
    """

    def decorator(func: Callable) -> Callable:
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = get_tracer(__name__)
            span_name = f"{func.__module__}.{func.__name__}"

            with tracer.start_as_current_span(
                span_name,
                attributes={
                    SpanAttributes.INPUT_VALUE: json.dumps({"args": args, "kwargs": kwargs}, default=str),
                    SpanAttributes.INPUT_MIME_TYPE: OpenInferenceMimeTypeValues.JSON.value,
                },
            ) as span:
                try:
                    result = await func(*args, **kwargs)
                    # Record output
                    span.set_attributes(
                        {
                            SpanAttributes.OUTPUT_VALUE: json.dumps(result, default=str),
                            SpanAttributes.OUTPUT_MIME_TYPE: OpenInferenceMimeTypeValues.JSON.value,
                        }
                    )
                    return result
                except Exception as e:
                    span.set_status(StatusCode.ERROR, str(e))
                    raise

        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = get_tracer(__name__)
            span_name = f"{func.__module__}.{func.__name__}"

            with tracer.start_as_current_span(
                span_name,
                attributes={
                    SpanAttributes.INPUT_VALUE: json.dumps({"args": args, "kwargs": kwargs}, default=str),
                    SpanAttributes.INPUT_MIME_TYPE: OpenInferenceMimeTypeValues.JSON.value,
                },
            ) as span:
                try:
                    result = func(*args, **kwargs)
                    # Record output
                    span.set_attributes(
                        {
                            SpanAttributes.OUTPUT_VALUE: json.dumps(result, default=str),
                            SpanAttributes.OUTPUT_MIME_TYPE: OpenInferenceMimeTypeValues.JSON.value,
                        }
                    )
                    return result
                except Exception as e:
                    span.set_status(StatusCode.ERROR, str(e))
                    raise

        # Decide which wrapper to return based on whether the function is async
        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper

    return decorator
