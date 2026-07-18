from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.events.pipeline.knowledge_teardown_requested_event import KnowledgeTeardownRequestedEvent
    from swiss_ai_hub.core.events.pipeline.source_updated_event import SourceUpdatedEvent

__all__ = [
    "KnowledgeTeardownRequestedEvent",
    "SourceUpdatedEvent",
]

_LAZY_IMPORTS: dict[str, str] = {
    "KnowledgeTeardownRequestedEvent": "swiss_ai_hub.core.events.pipeline.knowledge_teardown_requested_event",
    "SourceUpdatedEvent": "swiss_ai_hub.core.events.pipeline.source_updated_event",
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
