from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.events.base_event import BaseEvent
    from swiss_ai_hub.core.events.discovery.class_discovery_request_event import ClassDiscoveryRequestEvent
    from swiss_ai_hub.core.events.discovery.event_specs import EventSpecs

__all__ = [
    "BaseEvent",
    "ClassDiscoveryRequestEvent",
    "EventSpecs",
]

_LAZY_IMPORTS: dict[str, str] = {
    "BaseEvent": "swiss_ai_hub.core.events.base_event",
    "ClassDiscoveryRequestEvent": "swiss_ai_hub.core.events.discovery.class_discovery_request_event",
    "EventSpecs": "swiss_ai_hub.core.events.discovery.event_specs",
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
