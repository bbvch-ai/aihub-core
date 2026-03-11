from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.polling.js_poller import JSPoller
    from swiss_ai_hub.core.polling.polled_message import PolledMessage

__all__ = [
    "JSPoller",
    "PolledMessage",
]

_LAZY_IMPORTS: dict[str, str] = {
    "JSPoller": "swiss_ai_hub.core.polling.js_poller",
    "PolledMessage": "swiss_ai_hub.core.polling.polled_message",
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
