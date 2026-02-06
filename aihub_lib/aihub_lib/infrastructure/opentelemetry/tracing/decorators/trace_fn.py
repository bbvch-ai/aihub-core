import asyncio
import functools
import inspect
import io
import types
from collections.abc import AsyncGenerator, AsyncIterator, Callable, Generator, Iterator
from functools import lru_cache
from typing import Any, ParamSpec, TypeVar

from aihub_lib.infrastructure.opentelemetry.tracing.SmartTracer import get_tracer

P = ParamSpec("P")
T = TypeVar("T")


class TracingConfig:
    """Configuration for tracing behavior"""

    STRING_TRUNCATE_LENGTH = 500
    REPR_TRUNCATE_LENGTH = 100
    CONCISE_REPR_LENGTH = 50
    MAX_COLLECTION_ITEMS_FULL = 5
    MAX_DICT_ITEMS_FULL = 3
    SAMPLE_ITEMS_COUNT = 2
    SKIP_PARAMS = frozenset(("self", "cls"))


@lru_cache(maxsize=256)
def _is_optional_dependency_dangerous(type_name: str) -> bool:
    """
    Check type names ONLY for optional dependencies that might not be installed.
    """
    optional_dangerous_types = {
        # Data science libraries (might not be installed)
        "DataFrame",
        "Series",
        "ndarray",
        "Tensor",
        "Dataset",
        "DataLoader",
        # Database types from various optional DB libraries
        "Cursor",
        "Connection",
        "Session",
        "Transaction",
        "AsyncCursor",
        "AsyncConnection",
        "AsyncSession",
        # Response types from optional web frameworks
        "StreamingResponse",
        "FileResponse",
        "HTMLResponse",
        # Other specialized optional types
        "HTTPResponse",
        "HTTPSConnection",
        "Socket",
    }
    return type_name in optional_dangerous_types


def trace_fn[**P, T](func: Callable[P, T]) -> Callable[P, T]:
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

    # Pre-compute function metadata to avoid repeated computation
    func_qualname = func.__qualname__
    func_module = func.__module__ or __name__
    is_async = asyncio.iscoroutinefunction(func)

    # Pre-parse signature for better performance
    try:
        func_signature = inspect.signature(func)
    except (ValueError, TypeError):
        func_signature = None

    def _trace_execution(span, args, kwargs, is_async_execution=False):
        """Common tracing logic for both sync and async execution"""
        _trace_inputs(span, args, kwargs, func_signature)

        span.set_attribute("function.name", func_qualname)
        span.set_attribute("function.module", func_module)
        span.set_attribute("function.is_async", is_async_execution)

    def _handle_result(span, result):
        """Common result handling logic"""
        span.set_attribute("operation.success", True)
        _trace_output(span, result)
        return result

    def _handle_exception(span, exception):
        """Common exception handling logic"""
        span.set_attribute("operation.success", False)
        span.set_attribute("error.type", type(exception).__name__)
        _safe_set_attribute(span, "error.message", str(exception))
        span.record_exception(exception)

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs) -> Any:
        tracer = get_tracer(func_module)

        with tracer.start_as_current_span(func_qualname) as span:
            _trace_execution(span, args, kwargs, is_async_execution=True)

            try:
                result = await func(*args, **kwargs)
                return _handle_result(span, result)
            except Exception as e:
                _handle_exception(span, e)
                raise

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs) -> Any:
        tracer = get_tracer(func_module)

        with tracer.start_as_current_span(func_qualname) as span:
            _trace_execution(span, args, kwargs, is_async_execution=False)

            try:
                result = func(*args, **kwargs)
                return _handle_result(span, result)
            except Exception as e:
                _handle_exception(span, e)
                raise

    return async_wrapper if is_async else sync_wrapper


def _trace_inputs(span, args: tuple, kwargs: dict, func_signature: inspect.Signature | None = None) -> None:
    """Trace function inputs by trying to convert them to strings."""
    if func_signature:
        try:
            bound_args = func_signature.bind(*args, **kwargs)
            bound_args.apply_defaults()

            for param_name, param_value in bound_args.arguments.items():
                if param_name in TracingConfig.SKIP_PARAMS:
                    continue
                _safe_set_attribute(span, f"input.{param_name}", param_value)
            return
        except Exception:
            pass  # Fall through to fallback

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
    # Fast path for primitives
    if value is None or isinstance(value, bool | int | float):
        span.set_attribute(key, value)
        return

    if isinstance(value, str):
        if len(value) > TracingConfig.STRING_TRUNCATE_LENGTH:
            span.set_attribute(key, value[: TracingConfig.STRING_TRUNCATE_LENGTH] + "...")
        else:
            span.set_attribute(key, value)
        return

    if _is_dangerous_type(value):
        _set_type_name_attribute(span, key, value)
        return

    if isinstance(value, list | tuple):
        _handle_sequence_attribute(span, key, value)
        return

    if isinstance(value, dict):
        _handle_dict_attribute(span, key, value)
        return

    _handle_object_attribute(span, key, value)


def _is_dangerous_type(value: Any) -> bool:
    """
    Check if a value is a dangerous type that we should NOT try to convert to string.

    Uses a hybrid approach that:
    1. Properly handles inheritance using isinstance() with ABCs
    2. Uses duck-typing for file-like and cursor-like objects
    3. Only uses type name matching for optional dependencies

    This approach correctly identifies:
    - Subclasses of dangerous types (e.g., custom BytesIO subclasses)
    - Duck-typed objects (e.g., objects with file-like interfaces)
    - Standard dangerous types and their descendants
    """
    try:
        if value is None or isinstance(value, bool | int | float | str):
            return False

        if isinstance(value, bytes | bytearray | memoryview):
            return True

        if isinstance(value, io.IOBase):
            return True

        if isinstance(
            value,
            Iterator | AsyncIterator | Generator | AsyncGenerator | types.GeneratorType | types.AsyncGeneratorType,
        ):
            # These are technically iterators but safe to represent
            if not isinstance(
                value, str | list | tuple | dict | set | frozenset | range | enumerate | zip | map | filter
            ):
                return True

        # Duck-typing for file-like objects
        if hasattr(value, "read"):
            if hasattr(value, "seek") or hasattr(value, "write"):
                return True

            if hasattr(value, "status_code") or hasattr(value, "headers"):
                return True

        # Duck-typing for database cursors
        if hasattr(value, "execute") and hasattr(value, "fetchone"):
            return True

        # Only use type name checking for optional dependencies
        # that might not be installed (pandas, numpy, etc.)
        type_name = type(value).__name__
        if _is_optional_dependency_dangerous(type_name):
            return True

        return False

    except Exception:
        # If we can't determine safely, err on the side of caution
        return True


def _set_type_name_attribute(span, key: str, value: Any) -> None:
    """Set attribute with type name for dangerous types"""
    try:
        type_name = type(value).__name__
        if hasattr(value, "__len__"):
            try:
                size = len(value)
                span.set_attribute(key, f"[{type_name}(len={size})]")
            except Exception:
                span.set_attribute(key, f"[{type_name}]")
        else:
            span.set_attribute(key, f"[{type_name}]")
    except Exception:
        span.set_attribute(key, "[BINARY_OR_STREAM]")


def _handle_sequence_attribute(span, key: str, value: Any) -> None:
    """Handle list/tuple attributes efficiently"""
    try:
        length = len(value)
        is_list = isinstance(value, list)
        bracket_open = "[" if is_list else "("
        bracket_close = "]" if is_list else ")"

        if length == 0:
            span.set_attribute(key, f"{bracket_open}{bracket_close}")
        elif length <= TracingConfig.MAX_COLLECTION_ITEMS_FULL:
            items = [_get_concise_repr(item) for item in value]
            span.set_attribute(key, f"{bracket_open}{', '.join(items)}{bracket_close}")
        else:
            sample_items = [_get_concise_repr(value[i]) for i in range(min(TracingConfig.SAMPLE_ITEMS_COUNT, length))]
            span.set_attribute(key, f"{bracket_open}{', '.join(sample_items)}, ...{length} items{bracket_close}")
    except Exception:
        _handle_object_attribute(span, key, value)


def _handle_dict_attribute(span, key: str, value: dict) -> None:
    """Handle dictionary attributes efficiently"""
    try:
        length = len(value)

        if length == 0:
            span.set_attribute(key, "{}")
        elif length <= TracingConfig.MAX_DICT_ITEMS_FULL:
            items = []
            for k, v in list(value.items())[: TracingConfig.MAX_DICT_ITEMS_FULL]:
                key_repr = _get_concise_repr(k)
                val_repr = _get_concise_repr(v)
                items.append(f"{key_repr}: {val_repr}")
            span.set_attribute(key, f"{{{', '.join(items)}}}")
        else:
            # Just show count for large dicts
            span.set_attribute(key, f"{{...{length} items}}")
    except Exception:
        _handle_object_attribute(span, key, value)


def _handle_object_attribute(span, key: str, value: Any) -> None:
    """Handle general object attributes"""
    try:
        class_name = type(value).__name__
        if hasattr(value, "__dict__") or hasattr(value, "__slots__"):
            if hasattr(value, "__repr__"):
                try:
                    repr_str = repr(value)
                    if len(repr_str) <= TracingConfig.REPR_TRUNCATE_LENGTH and not repr_str.startswith("<"):
                        span.set_attribute(key, repr_str)
                        return
                except Exception:
                    pass
            span.set_attribute(key, class_name)
        else:
            str_value = str(value)
            if len(str_value) > TracingConfig.REPR_TRUNCATE_LENGTH:
                str_value = str_value[: TracingConfig.REPR_TRUNCATE_LENGTH] + "..."
            span.set_attribute(key, str_value)
    except Exception:
        try:
            type_name = type(value).__name__
            span.set_attribute(key, f"[{type_name}]")
        except Exception:
            span.set_attribute(key, "[NO_REPR]")


def _get_concise_repr(value: Any) -> str:
    """Get a concise representation of a value for use in collections."""
    try:
        if value is None:
            return "None"
        if isinstance(value, bool):
            return str(value)
        if isinstance(value, int | float):
            return str(value)
        if isinstance(value, str):
            if len(value) > TracingConfig.CONCISE_REPR_LENGTH:
                return f"'{value[: TracingConfig.CONCISE_REPR_LENGTH]}...'"
            return f"'{value}'"

        if _is_dangerous_type(value):
            return f"[{type(value).__name__}]"

        if hasattr(value, "__dict__") or hasattr(value, "__slots__"):
            return type(value).__name__

        # Other types
        str_val = str(value)
        if len(str_val) > TracingConfig.CONCISE_REPR_LENGTH:
            return str_val[: TracingConfig.CONCISE_REPR_LENGTH] + "..."
        return str_val

    except Exception:
        try:
            return f"[{type(value).__name__}]"
        except Exception:
            return "[NO_REPR]"
