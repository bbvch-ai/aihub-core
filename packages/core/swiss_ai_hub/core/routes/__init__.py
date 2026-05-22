from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.routes.chat.chat_service import ChatService, JsonResources, StreamingResources
    from swiss_ai_hub.core.routes.controller import Controller
    from swiss_ai_hub.core.routes.health.dto.health_response import ApiHealthChecks, HealthResponse, ProcessHealthChecks
    from swiss_ai_hub.core.routes.health.health_checks import (
        check_milvus,
        check_mongodb,
        check_nats,
        check_nats_sync,
        check_redis,
        check_redis_sync,
        check_s3,
    )
    from swiss_ai_hub.core.routes.health.health_controller import HealthController
    from swiss_ai_hub.core.routes.health.health_server import HealthCheckProvider, HealthServer
    from swiss_ai_hub.core.routes.tenant_scoped_controller import TenantScopedController

__all__ = [
    "check_s3",
    "check_redis_sync",
    "check_redis",
    "check_nats_sync",
    "check_nats",
    "check_mongodb",
    "check_milvus",
    "StreamingResources",
    "ProcessHealthChecks",
    "JsonResources",
    "HealthResponse",
    "ApiHealthChecks",
    "ChatService",
    "Controller",
    "HealthCheckProvider",
    "HealthController",
    "HealthServer",
    "TenantScopedController",
]

_HEALTH_CHECKS_MODULE = "swiss_ai_hub.core.routes.health.health_checks"
_CHAT_SERVICE_MODULE = "swiss_ai_hub.core.routes.chat.chat_service"
_HEALTH_RESPONSE_MODULE = "swiss_ai_hub.core.routes.health.dto.health_response"

_LAZY_IMPORTS = {
    "check_s3": _HEALTH_CHECKS_MODULE,
    "check_redis_sync": _HEALTH_CHECKS_MODULE,
    "check_redis": _HEALTH_CHECKS_MODULE,
    "check_nats_sync": _HEALTH_CHECKS_MODULE,
    "check_nats": _HEALTH_CHECKS_MODULE,
    "check_mongodb": _HEALTH_CHECKS_MODULE,
    "check_milvus": _HEALTH_CHECKS_MODULE,
    "StreamingResources": _CHAT_SERVICE_MODULE,
    "ProcessHealthChecks": _HEALTH_RESPONSE_MODULE,
    "JsonResources": _CHAT_SERVICE_MODULE,
    "HealthResponse": _HEALTH_RESPONSE_MODULE,
    "ApiHealthChecks": _HEALTH_RESPONSE_MODULE,
    "ChatService": _CHAT_SERVICE_MODULE,
    "Controller": "swiss_ai_hub.core.routes.controller",
    "HealthCheckProvider": "swiss_ai_hub.core.routes.health.health_server",
    "HealthController": "swiss_ai_hub.core.routes.health.health_controller",
    "HealthServer": "swiss_ai_hub.core.routes.health.health_server",
    "TenantScopedController": "swiss_ai_hub.core.routes.tenant_scoped_controller",
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        from importlib import import_module

        value = getattr(import_module(_LAZY_IMPORTS[name]), name)
        globals()[name] = value
        return value
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
