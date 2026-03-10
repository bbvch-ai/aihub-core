from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.infrastructure.api.AIHubSettings import AIHubSettings
    from swiss_ai_hub.core.infrastructure.api.DefaultTenantSettings import DefaultTenantSettings
    from swiss_ai_hub.core.infrastructure.api.UserSignupSettings import UserSignupSettings
    from swiss_ai_hub.core.infrastructure.langfuse.LangfuseProvisioner import LangfuseProvisioner
    from swiss_ai_hub.core.infrastructure.langfuse.LangfuseSettings import LangfuseSettings
    from swiss_ai_hub.core.infrastructure.litellm.LiteLLMProxySettings import LiteLLMProxySettings
    from swiss_ai_hub.core.infrastructure.litellm.LiteLLMService import LiteLLMService
    from swiss_ai_hub.core.infrastructure.logging.logger import enable_logging
    from swiss_ai_hub.core.infrastructure.milvus.MilvusSettings import MilvusSettings
    from swiss_ai_hub.core.infrastructure.milvus.use_milvus import use_milvus
    from swiss_ai_hub.core.infrastructure.milvus.use_vector_store_factory import use_vector_store_factory
    from swiss_ai_hub.core.infrastructure.mineru.MineruSettings import MineruSettings
    from swiss_ai_hub.core.infrastructure.mongo.MongoSettings import MongoSettings
    from swiss_ai_hub.core.infrastructure.nats.NatsSettings import NatsSettings
    from swiss_ai_hub.core.infrastructure.opentelemetry.AihubInstrumentor import AihubInstrumentor
    from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.no_trace import no_trace
    from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
    from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.SmartTracer import get_tracer
    from swiss_ai_hub.core.infrastructure.parsing.ParsingSettings import ParsingSettings
    from swiss_ai_hub.core.infrastructure.redis.RedisSettings import RedisSettings
    from swiss_ai_hub.core.infrastructure.redis.use_redis import use_redis
    from swiss_ai_hub.core.infrastructure.s3.S3StorageSettings import S3StorageSettings
    from swiss_ai_hub.core.infrastructure.s3.use_s3 import create_s3_filesystem, use_s3, use_s3_service

__all__ = [
    "AIHubSettings",
    "AihubInstrumentor",
    "DefaultTenantSettings",
    "LangfuseProvisioner",
    "LangfuseSettings",
    "LiteLLMProxySettings",
    "LiteLLMService",
    "MilvusSettings",
    "MineruSettings",
    "MongoSettings",
    "NatsSettings",
    "ParsingSettings",
    "RedisSettings",
    "S3StorageSettings",
    "UserSignupSettings",
    "create_s3_filesystem",
    "enable_logging",
    "get_tracer",
    "no_trace",
    "trace_fn",
    "use_milvus",
    "use_redis",
    "use_s3",
    "use_s3_service",
    "use_vector_store_factory",
]

_LAZY_IMPORTS = {
    "AIHubSettings": "swiss_ai_hub.core.infrastructure.api.AIHubSettings",
    "AihubInstrumentor": "swiss_ai_hub.core.infrastructure.opentelemetry.AihubInstrumentor",
    "DefaultTenantSettings": "swiss_ai_hub.core.infrastructure.api.DefaultTenantSettings",
    "LangfuseProvisioner": "swiss_ai_hub.core.infrastructure.langfuse.LangfuseProvisioner",
    "LangfuseSettings": "swiss_ai_hub.core.infrastructure.langfuse.LangfuseSettings",
    "LiteLLMProxySettings": "swiss_ai_hub.core.infrastructure.litellm.LiteLLMProxySettings",
    "LiteLLMService": "swiss_ai_hub.core.infrastructure.litellm.LiteLLMService",
    "MilvusSettings": "swiss_ai_hub.core.infrastructure.milvus.MilvusSettings",
    "MineruSettings": "swiss_ai_hub.core.infrastructure.mineru.MineruSettings",
    "MongoSettings": "swiss_ai_hub.core.infrastructure.mongo.MongoSettings",
    "NatsSettings": "swiss_ai_hub.core.infrastructure.nats.NatsSettings",
    "ParsingSettings": "swiss_ai_hub.core.infrastructure.parsing.ParsingSettings",
    "RedisSettings": "swiss_ai_hub.core.infrastructure.redis.RedisSettings",
    "S3StorageSettings": "swiss_ai_hub.core.infrastructure.s3.S3StorageSettings",
    "UserSignupSettings": "swiss_ai_hub.core.infrastructure.api.UserSignupSettings",
    "create_s3_filesystem": "swiss_ai_hub.core.infrastructure.s3.use_s3",
    "enable_logging": "swiss_ai_hub.core.infrastructure.logging.logger",
    "get_tracer": "swiss_ai_hub.core.infrastructure.opentelemetry.tracing.SmartTracer",
    "no_trace": "swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.no_trace",
    "trace_fn": "swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn",
    "use_milvus": "swiss_ai_hub.core.infrastructure.milvus.use_milvus",
    "use_redis": "swiss_ai_hub.core.infrastructure.redis.use_redis",
    "use_s3": "swiss_ai_hub.core.infrastructure.s3.use_s3",
    "use_s3_service": "swiss_ai_hub.core.infrastructure.s3.use_s3",
    "use_vector_store_factory": "swiss_ai_hub.core.infrastructure.milvus.use_vector_store_factory",
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        from importlib import import_module

        return getattr(import_module(_LAZY_IMPORTS[name]), name)
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
