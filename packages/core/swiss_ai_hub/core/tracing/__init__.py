from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.tracing.nats_message_headers import NATSMessageHeaders
    from swiss_ai_hub.core.tracing.nats_trace_context_propagator import NATSTraceContextPropagator

__all__ = [
    "NATSMessageHeaders",
    "NATSTraceContextPropagator",
]

_LAZY_IMPORTS: dict[str, str] = {
    "NATSMessageHeaders": "swiss_ai_hub.core.tracing.nats_message_headers",
    "NATSTraceContextPropagator": "swiss_ai_hub.core.tracing.nats_trace_context_propagator",
}


def __getattr__(name: str) -> object:
    if name in _LAZY_IMPORTS:
        import importlib

        module = importlib.import_module(_LAZY_IMPORTS[name])
        value = getattr(module, name)
        globals()[name] = value
        return value
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
