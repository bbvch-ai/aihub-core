from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.dispatcher.BaseDispatcher import BaseDispatcher, EventsAndKwargs
    from swiss_ai_hub.core.dispatcher.stores.event.ExecutionContextEventStore import ExecutionContextEventStore
    from swiss_ai_hub.core.dispatcher.stores.event.JetStreamEventStore import JetStreamEventStore
    from swiss_ai_hub.core.dispatcher.stores.step.StepStore import StepStore
    from swiss_ai_hub.core.dispatcher.stores.StoreBase import StoreBase
    from swiss_ai_hub.core.dispatcher.stores.trace.TraceStore import TraceStore

__all__ = [
    "BaseDispatcher",
    "EventsAndKwargs",
    "ExecutionContextEventStore",
    "JetStreamEventStore",
    "StepStore",
    "StoreBase",
    "TraceStore",
]

_LAZY_IMPORTS: dict[str, str] = {
    "BaseDispatcher": "swiss_ai_hub.core.dispatcher.BaseDispatcher",
    "EventsAndKwargs": "swiss_ai_hub.core.dispatcher.BaseDispatcher",
    "ExecutionContextEventStore": "swiss_ai_hub.core.dispatcher.stores.event.ExecutionContextEventStore",
    "JetStreamEventStore": "swiss_ai_hub.core.dispatcher.stores.event.JetStreamEventStore",
    "StepStore": "swiss_ai_hub.core.dispatcher.stores.step.StepStore",
    "StoreBase": "swiss_ai_hub.core.dispatcher.stores.StoreBase",
    "TraceStore": "swiss_ai_hub.core.dispatcher.stores.trace.TraceStore",
}


def __getattr__(name: str) -> object:
    if name in _LAZY_IMPORTS:
        import importlib

        module = importlib.import_module(_LAZY_IMPORTS[name])
        return getattr(module, name)
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
