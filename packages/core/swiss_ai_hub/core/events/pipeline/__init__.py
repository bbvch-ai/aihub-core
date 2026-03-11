from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.events.pipeline.SourceUpdatedEvent import SourceUpdatedEvent

__all__ = [
    "SourceUpdatedEvent",
]

_LAZY_IMPORTS: dict[str, str] = {
    "SourceUpdatedEvent": "swiss_ai_hub.core.events.pipeline.SourceUpdatedEvent",
}


def __getattr__(name: str) -> object:
    if name in _LAZY_IMPORTS:
        import importlib

        module = importlib.import_module(_LAZY_IMPORTS[name])
        return getattr(module, name)
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
