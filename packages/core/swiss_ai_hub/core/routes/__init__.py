from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.routes.chat.ChatService import ChatService
    from swiss_ai_hub.core.routes.Controller import Controller
    from swiss_ai_hub.core.routes.health.HealthController import HealthController
    from swiss_ai_hub.core.routes.health.HealthServer import HealthCheckProvider, HealthServer

__all__ = [
    "ChatService",
    "Controller",
    "HealthCheckProvider",
    "HealthController",
    "HealthServer",
]

_LAZY_IMPORTS = {
    "ChatService": "swiss_ai_hub.core.routes.chat.ChatService",
    "Controller": "swiss_ai_hub.core.routes.Controller",
    "HealthCheckProvider": "swiss_ai_hub.core.routes.health.HealthServer",
    "HealthController": "swiss_ai_hub.core.routes.health.HealthController",
    "HealthServer": "swiss_ai_hub.core.routes.health.HealthServer",
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        from importlib import import_module

        return getattr(import_module(_LAZY_IMPORTS[name]), name)
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
