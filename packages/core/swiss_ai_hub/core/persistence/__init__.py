from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.persistence.access.access_change_hook import AccessChangeHook
    from swiss_ai_hub.core.persistence.access.entities.bearer_token import BearerToken
    from swiss_ai_hub.core.persistence.access.entities.role_entity import (
        RoleEntity,
        UsageLimit,
    )
    from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity
    from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity
    from swiss_ai_hub.core.persistence.agents.agent_class_entity import AgentClassEntity
    from swiss_ai_hub.core.persistence.agents.agent_config_entity_document import AgentConfigEntityDocument
    from swiss_ai_hub.core.persistence.i18n.locale_string_entity import LocaleStringEntity
    from swiss_ai_hub.core.persistence.messaging.entities.persisted_agent_event_entity import (
        PersistedAgentEventEntity,
        Resolution,
        TimeRange,
    )
    from swiss_ai_hub.core.persistence.messaging.entities.persisted_process_event_entity import (
        PersistedProcessEventEntity,
    )
    from swiss_ai_hub.core.persistence.messaging.entities.thread_entity import (
        AgentInstanceRef,
        ThreadEntity,
        User,
    )
    from swiss_ai_hub.core.persistence.messaging.entities.types.event_bucket import EventBucket
    from swiss_ai_hub.core.persistence.notification.notification_entity import NotificationEntity
    from swiss_ai_hub.core.persistence.process.process_class_entity import (
        AgentInSpecsEntity,
        HumanInSpecsEntity,
        ProcessClassEntity,
        ProgramInSpecsEntity,
    )
    from swiss_ai_hub.core.persistence.process.process_config_entity_document import ProcessConfigEntityDocument
    from swiss_ai_hub.core.persistence.rag.datalake.entities.bucket_entity import BucketEntity
    from swiss_ai_hub.core.persistence.rag.datalake.entities.namespace_entity import NamespaceEntity
    from swiss_ai_hub.core.persistence.rag.documents.entities.ref_doc import RefDoc
    from swiss_ai_hub.core.persistence.rag.documents.stores.docstore import create_mongo_document_store
    from swiss_ai_hub.core.persistence.rag.vectors import VectorStoreFactory
    from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import (
        CREATED_AT,
        DOCUMENT_ID,
        DOCUMENT_STORE_NAME,
        DOCUMENT_TITLE,
        H1,
        H2,
        H3,
        H4,
        H5,
        H6,
        HASH,
        INDEX,
        INSERTED_AT,
        IS_INGESTED,
        LANGUAGE,
        NAMESPACE,
        NODE_CONTENT_TYPE,
        NODE_CONTENT_TYPE_FIGURE,
        NODE_CONTENT_TYPE_TEXT,
        NODE_TYPE_CONTENT,
        NODE_TYPE_SUMMARY,
        PAGE,
        REFERENCE_NAME,
        REFERENCE_URL,
        SECTION_END_LINE,
        SECTION_START_LINE,
        SOURCE,
        SOURCE_ORIGIN,
        TYPE,
        UPDATED_AT,
        VERSION,
        NodeTypeValue,
    )
    from swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_partition_manager import (
        get_partition_name_for_namespace,
    )
    from swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_vector_store_config import MilvusVectorStoreConfig
    from swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_vector_store_factory import (
        MilvusIndexType,
        create_milvus_vector_store,
    )
    from swiss_ai_hub.core.persistence.user.user_dashboard_entity import UserDashboardEntity
    from swiss_ai_hub.core.persistence.utils import str_to_object_id

__all__ = [
    "AccessChangeHook",
    "AgentClassEntity",
    "AgentConfigEntityDocument",
    "AgentInSpecsEntity",
    "AgentInstanceRef",
    "BearerToken",
    "BucketEntity",
    "CREATED_AT",
    "DOCUMENT_ID",
    "DOCUMENT_STORE_NAME",
    "DOCUMENT_TITLE",
    "EventBucket",
    "H1",
    "H2",
    "H3",
    "H4",
    "H5",
    "H6",
    "HASH",
    "HumanInSpecsEntity",
    "INDEX",
    "INSERTED_AT",
    "IS_INGESTED",
    "LANGUAGE",
    "LocaleStringEntity",
    "MilvusIndexType",
    "MilvusVectorStoreConfig",
    "NAMESPACE",
    "NODE_CONTENT_TYPE",
    "NODE_CONTENT_TYPE_FIGURE",
    "NODE_CONTENT_TYPE_TEXT",
    "NODE_TYPE_CONTENT",
    "NODE_TYPE_SUMMARY",
    "NamespaceEntity",
    "NodeTypeValue",
    "NotificationEntity",
    "PAGE",
    "PersistedAgentEventEntity",
    "PersistedProcessEventEntity",
    "ProcessClassEntity",
    "ProcessConfigEntityDocument",
    "ProgramInSpecsEntity",
    "REFERENCE_NAME",
    "REFERENCE_URL",
    "RefDoc",
    "Resolution",
    "RoleEntity",
    "SECTION_END_LINE",
    "SECTION_START_LINE",
    "SOURCE",
    "SOURCE_ORIGIN",
    "TYPE",
    "TenantMetadataEntity",
    "ThreadEntity",
    "TimeRange",
    "UPDATED_AT",
    "UsageLimit",
    "User",
    "UserDashboardEntity",
    "UserTenantRoleEntity",
    "VERSION",
    "VectorStoreFactory",
    "create_milvus_vector_store",
    "create_mongo_document_store",
    "get_partition_name_for_namespace",
    "str_to_object_id",
]

_NODE_METADATA_MODULE = "swiss_ai_hub.core.persistence.rag.vectors.node_metadata"
_PROCESS_CLASS_ENTITY_MODULE = "swiss_ai_hub.core.persistence.process.process_class_entity"
_THREAD_ENTITY_MODULE = "swiss_ai_hub.core.persistence.messaging.entities.thread_entity"
_PERSISTED_AGENT_EVENT_MODULE = "swiss_ai_hub.core.persistence.messaging.entities.persisted_agent_event_entity"

_LAZY_IMPORTS = {
    "AccessChangeHook": "swiss_ai_hub.core.persistence.access.access_change_hook",
    "AgentClassEntity": "swiss_ai_hub.core.persistence.agents.agent_class_entity",
    "AgentConfigEntityDocument": "swiss_ai_hub.core.persistence.agents.agent_config_entity_document",
    "AgentInSpecsEntity": _PROCESS_CLASS_ENTITY_MODULE,
    "AgentInstanceRef": _THREAD_ENTITY_MODULE,
    "BearerToken": "swiss_ai_hub.core.persistence.access.entities.bearer_token",
    "BucketEntity": "swiss_ai_hub.core.persistence.rag.datalake.entities.bucket_entity",
    "CREATED_AT": _NODE_METADATA_MODULE,
    "DOCUMENT_ID": _NODE_METADATA_MODULE,
    "DOCUMENT_STORE_NAME": _NODE_METADATA_MODULE,
    "DOCUMENT_TITLE": _NODE_METADATA_MODULE,
    "EventBucket": "swiss_ai_hub.core.persistence.messaging.entities.types.event_bucket",
    "H1": _NODE_METADATA_MODULE,
    "H2": _NODE_METADATA_MODULE,
    "H3": _NODE_METADATA_MODULE,
    "H4": _NODE_METADATA_MODULE,
    "H5": _NODE_METADATA_MODULE,
    "H6": _NODE_METADATA_MODULE,
    "HASH": _NODE_METADATA_MODULE,
    "HumanInSpecsEntity": _PROCESS_CLASS_ENTITY_MODULE,
    "INDEX": _NODE_METADATA_MODULE,
    "INSERTED_AT": _NODE_METADATA_MODULE,
    "IS_INGESTED": _NODE_METADATA_MODULE,
    "LANGUAGE": _NODE_METADATA_MODULE,
    "LocaleStringEntity": "swiss_ai_hub.core.persistence.i18n.locale_string_entity",
    "MilvusIndexType": "swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_vector_store_factory",
    "MilvusVectorStoreConfig": "swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_vector_store_config",
    "NAMESPACE": _NODE_METADATA_MODULE,
    "NODE_CONTENT_TYPE": _NODE_METADATA_MODULE,
    "NODE_CONTENT_TYPE_FIGURE": _NODE_METADATA_MODULE,
    "NODE_CONTENT_TYPE_TEXT": _NODE_METADATA_MODULE,
    "NODE_TYPE_CONTENT": _NODE_METADATA_MODULE,
    "NODE_TYPE_SUMMARY": _NODE_METADATA_MODULE,
    "NamespaceEntity": "swiss_ai_hub.core.persistence.rag.datalake.entities.namespace_entity",
    "NodeTypeValue": _NODE_METADATA_MODULE,
    "NotificationEntity": "swiss_ai_hub.core.persistence.notification.notification_entity",
    "PAGE": _NODE_METADATA_MODULE,
    "PersistedAgentEventEntity": _PERSISTED_AGENT_EVENT_MODULE,
    "PersistedProcessEventEntity": "swiss_ai_hub.core.persistence.messaging.entities.persisted_process_event_entity",
    "ProcessClassEntity": _PROCESS_CLASS_ENTITY_MODULE,
    "ProcessConfigEntityDocument": "swiss_ai_hub.core.persistence.process.process_config_entity_document",
    "ProgramInSpecsEntity": _PROCESS_CLASS_ENTITY_MODULE,
    "REFERENCE_NAME": _NODE_METADATA_MODULE,
    "REFERENCE_URL": _NODE_METADATA_MODULE,
    "RefDoc": "swiss_ai_hub.core.persistence.rag.documents.entities.ref_doc",
    "Resolution": _PERSISTED_AGENT_EVENT_MODULE,
    "RoleEntity": "swiss_ai_hub.core.persistence.access.entities.role_entity",
    "SECTION_END_LINE": _NODE_METADATA_MODULE,
    "SECTION_START_LINE": _NODE_METADATA_MODULE,
    "SOURCE": _NODE_METADATA_MODULE,
    "SOURCE_ORIGIN": _NODE_METADATA_MODULE,
    "TYPE": _NODE_METADATA_MODULE,
    "TenantMetadataEntity": "swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity",
    "ThreadEntity": _THREAD_ENTITY_MODULE,
    "TimeRange": _PERSISTED_AGENT_EVENT_MODULE,
    "UPDATED_AT": _NODE_METADATA_MODULE,
    "UsageLimit": "swiss_ai_hub.core.persistence.access.entities.role_entity",
    "User": _THREAD_ENTITY_MODULE,
    "UserDashboardEntity": "swiss_ai_hub.core.persistence.user.user_dashboard_entity",
    "UserTenantRoleEntity": "swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity",
    "VERSION": _NODE_METADATA_MODULE,
    "VectorStoreFactory": "swiss_ai_hub.core.persistence.rag.vectors",
    "create_milvus_vector_store": "swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_vector_store_factory",
    "create_mongo_document_store": "swiss_ai_hub.core.persistence.rag.documents.stores.docstore",
    "get_partition_name_for_namespace": "swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_partition_manager",
    "str_to_object_id": "swiss_ai_hub.core.persistence.utils",
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        from importlib import import_module

        value = getattr(import_module(_LAZY_IMPORTS[name]), name)
        globals()[name] = value
        return value
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
