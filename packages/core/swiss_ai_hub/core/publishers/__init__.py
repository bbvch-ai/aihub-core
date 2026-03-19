from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.publishers.abstract_publisher import AbstractPublisher
    from swiss_ai_hub.core.publishers.js_publisher import JSPublisher
    from swiss_ai_hub.core.publishers.nc_publisher import NCPublisher

__all__ = [
    "AbstractPublisher",
    "JSPublisher",
    "NCPublisher",
]

_LAZY_IMPORTS: dict[str, str] = {
    "AbstractPublisher": "swiss_ai_hub.core.publishers.abstract_publisher",
    "JSPublisher": "swiss_ai_hub.core.publishers.js_publisher",
    "NCPublisher": "swiss_ai_hub.core.publishers.nc_publisher",
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
