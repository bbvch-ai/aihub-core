from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.routes.chat.chat_service import (
        DISPLAY_STREAM_DRAIN_GRACE_SECONDS,
        ChatService,
        JsonResources,
        StreamingResources,
    )
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
    "DISPLAY_STREAM_DRAIN_GRACE_SECONDS",
    "Controller",
    "HealthCheckProvider",
    "HealthController",
    "HealthServer",
    "TenantScopedController",
]

_LAZY_IMPORTS = {
    "check_s3": "swiss_ai_hub.core.routes.health.health_checks",
    "check_redis_sync": "swiss_ai_hub.core.routes.health.health_checks",
    "check_redis": "swiss_ai_hub.core.routes.health.health_checks",
    "check_nats_sync": "swiss_ai_hub.core.routes.health.health_checks",
    "check_nats": "swiss_ai_hub.core.routes.health.health_checks",
    "check_mongodb": "swiss_ai_hub.core.routes.health.health_checks",
    "check_milvus": "swiss_ai_hub.core.routes.health.health_checks",
    "StreamingResources": "swiss_ai_hub.core.routes.chat.chat_service",
    "ProcessHealthChecks": "swiss_ai_hub.core.routes.health.dto.health_response",
    "JsonResources": "swiss_ai_hub.core.routes.chat.chat_service",
    "HealthResponse": "swiss_ai_hub.core.routes.health.dto.health_response",
    "ApiHealthChecks": "swiss_ai_hub.core.routes.health.dto.health_response",
    "ChatService": "swiss_ai_hub.core.routes.chat.chat_service",
    "DISPLAY_STREAM_DRAIN_GRACE_SECONDS": "swiss_ai_hub.core.routes.chat.chat_service",
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
