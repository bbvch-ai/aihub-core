from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.polling.JSPoller import JSPoller
    from swiss_ai_hub.core.polling.PolledMessage import PolledMessage

__all__ = [
    "JSPoller",
    "PolledMessage",
]

_LAZY_IMPORTS: dict[str, str] = {
    "JSPoller": "swiss_ai_hub.core.polling.JSPoller",
    "PolledMessage": "swiss_ai_hub.core.polling.PolledMessage",
}


def __getattr__(name: str) -> object:
    if name in _LAZY_IMPORTS:
        import importlib

        module = importlib.import_module(_LAZY_IMPORTS[name])
        return getattr(module, name)
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
