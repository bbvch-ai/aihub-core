import asyncio
import functools
import inspect
from collections.abc import Callable
from typing import Any

from aihub_lib.infrastructure.opentelemetry.tracing.SmartTracer import get_tracer


def trace_fn(func: Callable) -> Callable:
    """
    A completely generic decorator that traces any function with its inputs and outputs.

    Features:
    - Automatically derives span name from function.__qualname__
    - Tries to convert all inputs to string/repr, falls back to [NO_REPR]
    - Tries to convert outputs to string/repr, falls back to [NO_REPR]
    - Works with both sync and async functions
    - Zero coupling to specific domains or types
    - Follows KISS principle
    """

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs) -> Any:
        tracer = get_tracer(__name__)
        span_name = func.__qualname__

        with tracer.start_as_current_span(span_name) as span:
            # Trace inputs
            _trace_inputs(span, func, args, kwargs)

            try:
                result = await func(*args, **kwargs)
                span.set_attribute("operation.success", True)

                # Trace output
                _trace_output(span, result)

                return result
            except Exception as e:
                span.set_attribute("success", False)
                span.set_attribute("error.type", type(e).__name__)
                _safe_set_attribute(span, "error.message", str(e))
                span.record_exception(e)
                raise

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs) -> Any:
        tracer = get_tracer(__name__)
        span_name = func.__qualname__

        with tracer.start_as_current_span(span_name) as span:
            # Trace inputs
            _trace_inputs(span, func, args, kwargs)

            try:
                result = func(*args, **kwargs)
                span.set_attribute("operation.success", True)

                # Trace output
                _trace_output(span, result)

                return result
            except Exception as e:
                span.set_attribute("success", False)
                span.set_attribute("error.type", type(e).__name__)
                _safe_set_attribute(span, "error.message", str(e))
                span.record_exception(e)
                raise

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


def _trace_inputs(span, func: Callable, args: tuple, kwargs: dict) -> None:
    """Trace function inputs by trying to convert them to strings."""
    # Get parameter names
    try:
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()

        for param_name, param_value in bound_args.arguments.items():
            # Optionally skip self/cls parameters
            if param_name in ("self", "cls"):
                continue
            _safe_set_attribute(span, f"input.{param_name}", param_value)
    except Exception:
        # Fallback: trace positional and keyword args without names
        for i, arg in enumerate(args):
            _safe_set_attribute(span, f"input.arg_{i}", arg)

        for k, v in kwargs.items():
            _safe_set_attribute(span, f"input.{k}", v)


def _trace_output(span, result: Any) -> None:
    """Trace function output by trying to convert it to string."""
    _safe_set_attribute(span, "output.result", result)


def _safe_set_attribute(span, key: str, value: Any) -> None:
    """
    Safely set a span attribute with concise, readable representations.
    Handles binary data, streams, and large objects safely.
    Falls back to [NO_REPR] if all attempts fail.
    """
    try:
        # Handle primitives directly
        if isinstance(value, str | int | float | bool) or value is None:
            # Truncate very long strings to avoid bloating traces
            if isinstance(value, str) and len(value) > 500:
                span.set_attribute(key, value[:500] + "...")
            else:
                span.set_attribute(key, value)
            return
    except Exception:
        pass

    # Check for dangerous types that we should NOT try to convert
    if _is_dangerous_type(value):
        try:
            type_name = type(value).__name__
            span.set_attribute(key, f"[{type_name}]")
            return
        except Exception:
            span.set_attribute(key, "[BINARY_OR_STREAM]")
            return

    try:
        # Handle collections with concise representation
        if isinstance(value, list | tuple):
            if len(value) == 0:
                span.set_attribute(key, "[]" if isinstance(value, list) else "()")
                return
            elif len(value) <= 5:
                # Show concise representation of small collections
                items = []
                for item in value:
                    items.append(_get_concise_repr(item))
                bracket_open = "[" if isinstance(value, list) else "("
                bracket_close = "]" if isinstance(value, list) else ")"
                span.set_attribute(key, f"{bracket_open}{', '.join(items)}{bracket_close}")
                return
            else:
                # For large collections, show count and sample
                sample_items = [_get_concise_repr(item) for item in value[:2]]
                bracket_open = "[" if isinstance(value, list) else "("
                bracket_close = "]" if isinstance(value, list) else ")"
                span.set_attribute(
                    key, f"{bracket_open}{', '.join(sample_items)}, ...{len(value)} items{bracket_close}"
                )
                return
    except Exception:
        pass

    try:
        # Handle dictionaries
        if isinstance(value, dict):
            if len(value) == 0:
                span.set_attribute(key, "{}")
                return
            elif len(value) <= 3:
                items = []
                for k, v in list(value.items())[:3]:
                    key_repr = _get_concise_repr(k)
                    val_repr = _get_concise_repr(v)
                    items.append(f"{key_repr}: {val_repr}")
                span.set_attribute(key, f"{{{', '.join(items)}}}")
                return
            else:
                span.set_attribute(key, f"{{...{len(value)} items}}")
                return
    except Exception:
        pass

    try:
        # For class instances, just show the class name
        class_name = type(value).__name__
        # Check if it's likely a custom class (not a built-in type)
        if hasattr(value, "__dict__") or hasattr(value, "__slots__"):
            span.set_attribute(key, class_name)
            return
        else:
            # For built-in types, try str() but with safety checks
            str_value = str(value)
            if len(str_value) > 100:
                str_value = str_value[:100] + "..."
            span.set_attribute(key, str_value)
            return
    except Exception:
        pass

    try:
        # Fallback to type name
        type_name = type(value).__name__
        span.set_attribute(key, f"[{type_name}]")
        return
    except Exception:
        pass

    # Complete fallback
    span.set_attribute(key, "[NO_REPR]")


def _is_dangerous_type(value: Any) -> bool:
    """
    Check if a value is a dangerous type that we should NOT try to convert to string.
    This includes binary data, streams, generators, and other types that could:
    - Consume the stream/generator
    - Generate massive strings
    - Block for long periods
    - Use excessive memory
    """
    try:
        # Check by type name for common dangerous types
        type_name = type(value).__name__
        dangerous_type_names = {
            # Binary data
            "bytes",
            "bytearray",
            "memoryview",
            # Streams and responses
            "StreamingResponse",
            "HttpxBinaryResponseContent",
            "Response",
            # Generators and iterators
            "generator",
            "async_generator",
            "GeneratorType",
            "AsyncGeneratorType",
            "map",
            "filter",
            "zip",
            "enumerate",
            "range",
            # File-like objects
            "TextIOWrapper",
            "BufferedReader",
            "BufferedWriter",
            "BytesIO",
            "StringIO",
            # Database cursors and connections
            "Cursor",
            "Connection",
            "Session",
            # Large data structures
            "DataFrame",
            "Series",
            "ndarray",  # pandas/numpy
        }

        if type_name in dangerous_type_names:
            return True

        # Check if it's a generator or iterator by looking for __iter__ and __next__
        if hasattr(value, "__iter__") and hasattr(value, "__next__"):
            return True

        # Check if it's an async generator
        if hasattr(value, "__aiter__") and hasattr(value, "__anext__"):
            return True

        # Check if it looks like binary data (has bytes-like interface)
        if hasattr(value, "read") and hasattr(value, "seek"):
            return True

        return False

    except Exception:
        # If we can't determine safely, err on the side of caution
        return True


def _get_concise_repr(value: Any) -> str:
    """Get a concise representation of a value for use in collections."""
    try:
        if isinstance(value, str | int | float | bool) or value is None:
            str_val = str(value)
            return str_val[:50] + "..." if len(str_val) > 50 else str_val
        elif _is_dangerous_type(value):
            # Don't try to convert dangerous types
            return f"[{type(value).__name__}]"
        elif hasattr(value, "__dict__") or hasattr(value, "__slots__"):
            # Custom class instance
            return type(value).__name__
        else:
            # Built-in type, try str but keep it short
            str_val = str(value)
            return str_val[:50] + "..." if len(str_val) > 50 else str_val
    except Exception:
        try:
            return f"[{type(value).__name__}]"
        except Exception:
            return "[NO_REPR]"
