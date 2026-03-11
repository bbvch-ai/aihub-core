from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.events.BaseEvent import BaseEvent
    from swiss_ai_hub.core.events.discovery.ClassDiscoveryRequestEvent import ClassDiscoveryRequestEvent
    from swiss_ai_hub.core.events.discovery.EventSpecs import EventSpecs

__all__ = [
    "BaseEvent",
    "ClassDiscoveryRequestEvent",
    "EventSpecs",
]

_LAZY_IMPORTS: dict[str, str] = {
    "BaseEvent": "swiss_ai_hub.core.events.BaseEvent",
    "ClassDiscoveryRequestEvent": "swiss_ai_hub.core.events.discovery.ClassDiscoveryRequestEvent",
    "EventSpecs": "swiss_ai_hub.core.events.discovery.EventSpecs",
}


def __getattr__(name: str) -> object:
    if name in _LAZY_IMPORTS:
        import importlib

        module = importlib.import_module(_LAZY_IMPORTS[name])
        return getattr(module, name)
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
