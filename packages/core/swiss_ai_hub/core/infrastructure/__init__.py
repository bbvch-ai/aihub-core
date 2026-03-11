from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
    from swiss_ai_hub.core.infrastructure.api.default_tenant_settings import DefaultTenantSettings
    from swiss_ai_hub.core.infrastructure.api.user_signup_settings import UserSignupSettings
    from swiss_ai_hub.core.infrastructure.langfuse.langfuse_provisioner import LangfuseProvisioner
    from swiss_ai_hub.core.infrastructure.langfuse.langfuse_settings import LangfuseSettings
    from swiss_ai_hub.core.infrastructure.litellm.lite_llm_proxy_settings import LiteLLMProxySettings
    from swiss_ai_hub.core.infrastructure.litellm.lite_llm_service import LiteLLMService
    from swiss_ai_hub.core.infrastructure.logging.logger import enable_logging
    from swiss_ai_hub.core.infrastructure.milvus.milvus_settings import MilvusSettings
    from swiss_ai_hub.core.infrastructure.milvus.use_milvus import use_milvus
    from swiss_ai_hub.core.infrastructure.milvus.use_vector_store_factory import use_vector_store_factory
    from swiss_ai_hub.core.infrastructure.mineru.mineru_settings import MineruSettings
    from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
    from swiss_ai_hub.core.infrastructure.nats.nats_settings import NatsSettings
    from swiss_ai_hub.core.infrastructure.opentelemetry.aihub_instrumentor import AihubInstrumentor
    from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.no_trace import no_trace
    from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
    from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.smart_tracer import get_tracer
    from swiss_ai_hub.core.infrastructure.parsing.parsing_settings import ParsingSettings
    from swiss_ai_hub.core.infrastructure.redis.redis_settings import RedisSettings
    from swiss_ai_hub.core.infrastructure.redis.use_redis import use_redis
    from swiss_ai_hub.core.infrastructure.s3.s3_storage_settings import S3StorageSettings
    from swiss_ai_hub.core.infrastructure.s3.use_s3 import create_s3_filesystem, use_s3, use_s3_service
    from swiss_ai_hub.core.infrastructure.azure_data_lake.azure_data_lake_settings import AzureDataLakeSettings
    from swiss_ai_hub.core.infrastructure.azure_cognitive_services.azure_document_intelligence_settings import AzureDocumentIntelligenceSettings
    from swiss_ai_hub.core.infrastructure.mem0.types.memory import Memory
    from swiss_ai_hub.core.infrastructure.mem0.types.memory_relation import MemoryRelation
    from swiss_ai_hub.core.infrastructure.opentelemetry.open_telemetry_settings import OpenTelemetrySettings
    from swiss_ai_hub.core.infrastructure.sharepoint.share_point_settings import SharePointSettings
    from swiss_ai_hub.core.infrastructure.rclone.rclone_source_factory import azure_blob_source
    from swiss_ai_hub.core.infrastructure.rclone.rclone_source_factory import google_drive_source
    from swiss_ai_hub.core.infrastructure.rclone.rclone_source_factory import onedrive_source
    from swiss_ai_hub.core.infrastructure.rclone.rclone_source_factory import s3_source
    from swiss_ai_hub.core.infrastructure.rclone.rclone_source_factory import sftp_source
    from swiss_ai_hub.core.infrastructure.rclone.rclone_source_factory import sharepoint_source

__all__ = [
    "sharepoint_source",
    "sftp_source",
    "s3_source",
    "onedrive_source",
    "google_drive_source",
    "azure_blob_source",
    "SharePointSettings",
    "OpenTelemetrySettings",
    "MemoryRelation",
    "Memory",
    "AzureDocumentIntelligenceSettings",
    "AzureDataLakeSettings",
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
    "sharepoint_source": "swiss_ai_hub.core.infrastructure.rclone.rclone_source_factory",
    "sftp_source": "swiss_ai_hub.core.infrastructure.rclone.rclone_source_factory",
    "s3_source": "swiss_ai_hub.core.infrastructure.rclone.rclone_source_factory",
    "onedrive_source": "swiss_ai_hub.core.infrastructure.rclone.rclone_source_factory",
    "google_drive_source": "swiss_ai_hub.core.infrastructure.rclone.rclone_source_factory",
    "azure_blob_source": "swiss_ai_hub.core.infrastructure.rclone.rclone_source_factory",
    "SharePointSettings": "swiss_ai_hub.core.infrastructure.sharepoint.share_point_settings",
    "OpenTelemetrySettings": "swiss_ai_hub.core.infrastructure.opentelemetry.open_telemetry_settings",
    "MemoryRelation": "swiss_ai_hub.core.infrastructure.mem0.types.memory_relation",
    "Memory": "swiss_ai_hub.core.infrastructure.mem0.types.memory",
    "AzureDocumentIntelligenceSettings": "swiss_ai_hub.core.infrastructure.azure_cognitive_services.azure_document_intelligence_settings",
    "AzureDataLakeSettings": "swiss_ai_hub.core.infrastructure.azure_data_lake.azure_data_lake_settings",
    "AIHubSettings": "swiss_ai_hub.core.infrastructure.api.ai_hub_settings",
    "AihubInstrumentor": "swiss_ai_hub.core.infrastructure.opentelemetry.aihub_instrumentor",
    "DefaultTenantSettings": "swiss_ai_hub.core.infrastructure.api.default_tenant_settings",
    "LangfuseProvisioner": "swiss_ai_hub.core.infrastructure.langfuse.langfuse_provisioner",
    "LangfuseSettings": "swiss_ai_hub.core.infrastructure.langfuse.langfuse_settings",
    "LiteLLMProxySettings": "swiss_ai_hub.core.infrastructure.litellm.lite_llm_proxy_settings",
    "LiteLLMService": "swiss_ai_hub.core.infrastructure.litellm.lite_llm_service",
    "MilvusSettings": "swiss_ai_hub.core.infrastructure.milvus.milvus_settings",
    "MineruSettings": "swiss_ai_hub.core.infrastructure.mineru.mineru_settings",
    "MongoSettings": "swiss_ai_hub.core.infrastructure.mongo.mongo_settings",
    "NatsSettings": "swiss_ai_hub.core.infrastructure.nats.nats_settings",
    "ParsingSettings": "swiss_ai_hub.core.infrastructure.parsing.parsing_settings",
    "RedisSettings": "swiss_ai_hub.core.infrastructure.redis.redis_settings",
    "S3StorageSettings": "swiss_ai_hub.core.infrastructure.s3.s3_storage_settings",
    "UserSignupSettings": "swiss_ai_hub.core.infrastructure.api.user_signup_settings",
    "create_s3_filesystem": "swiss_ai_hub.core.infrastructure.s3.use_s3",
    "enable_logging": "swiss_ai_hub.core.infrastructure.logging.logger",
    "get_tracer": "swiss_ai_hub.core.infrastructure.opentelemetry.tracing.smart_tracer",
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

        value = getattr(import_module(_LAZY_IMPORTS[name]), name)
        globals()[name] = value
        return value
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
