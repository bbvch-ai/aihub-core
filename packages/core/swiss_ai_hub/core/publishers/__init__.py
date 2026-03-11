from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.publishers.AbstractPublisher import AbstractPublisher
    from swiss_ai_hub.core.publishers.JSPublisher import JSPublisher
    from swiss_ai_hub.core.publishers.NCPublisher import NCPublisher

__all__ = [
    "AbstractPublisher",
    "JSPublisher",
    "NCPublisher",
]

_LAZY_IMPORTS: dict[str, str] = {
    "AbstractPublisher": "swiss_ai_hub.core.publishers.AbstractPublisher",
    "JSPublisher": "swiss_ai_hub.core.publishers.JSPublisher",
    "NCPublisher": "swiss_ai_hub.core.publishers.NCPublisher",
}


def __getattr__(name: str) -> object:
    if name in _LAZY_IMPORTS:
        import importlib

        module = importlib.import_module(_LAZY_IMPORTS[name])
        return getattr(module, name)
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
