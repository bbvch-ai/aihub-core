from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.api.sockets.manager.web_socket_manager import WebSocketManager
    from swiss_ai_hub.api.sockets.sender.web_socket_sender import WebSocketSender

__all__ = [
    "WebSocketManager",
    "WebSocketSender",
]

_LAZY_IMPORTS: dict[str, str] = {
    "WebSocketManager": "swiss_ai_hub.api.sockets.manager.web_socket_manager",
    "WebSocketSender": "swiss_ai_hub.api.sockets.sender.web_socket_sender",
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
