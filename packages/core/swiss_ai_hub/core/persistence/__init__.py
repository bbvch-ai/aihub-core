from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.persistence.access.entities.bearer_token import BearerToken
    from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity, UsageLimit
    from swiss_ai_hub.core.persistence.access.entities.tenant_entity import TenantEntity
    from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity
    from swiss_ai_hub.core.persistence.agents.agent_class_entity import AgentClassEntity
    from swiss_ai_hub.core.persistence.agents.agent_config_entity_document import AgentConfigEntityDocument
    from swiss_ai_hub.core.persistence.i18n.locale_string_entity import LocaleStringEntity
    from swiss_ai_hub.core.persistence.messaging.entities.persisted_agent_event_entity import (
    from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import CREATED_AT
    from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import DOCUMENT_ID
    from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import DOCUMENT_STORE_NAME
    from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import DOCUMENT_TITLE
    from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import H1
    from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import H2
    from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import H3
    from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import H4
    from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import H5
    from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import H6
    from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import HASH
    from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import INDEX
    from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import INSERTED_AT
    from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import IS_INGESTED
    from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import LANGUAGE
    from swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_vector_store_factory import MilvusIndexType
    from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import NAMESPACE
    from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import NODE_CONTENT_TYPE
    from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import NODE_CONTENT_TYPE_FIGURE
    from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import NODE_CONTENT_TYPE_TEXT
    from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import NODE_TYPE_CONTENT
    from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import NODE_TYPE_SUMMARY
    from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import NodeTypeValue
    from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import PAGE
    from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import REFERENCE_NAME
    from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import REFERENCE_URL
    from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import SECTION_END_LINE
    from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import SECTION_START_LINE
    from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import SOURCE
    from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import SOURCE_ORIGIN
    from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import TYPE
    from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import UPDATED_AT
    from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import VERSION
    from swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_vector_store_factory import create_milvus_vector_store
    from swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_partition_manager import get_partition_name_for_namespace
    from swiss_ai_hub.core.persistence.process.process_class_entity import AgentInSpecsEntity
    from swiss_ai_hub.core.persistence.user.user_entity import DashboardItem
    from swiss_ai_hub.core.persistence.process.process_class_entity import HumanInSpecsEntity
    from swiss_ai_hub.core.persistence.messaging.entities.persisted_agent_event_entity import PersistedAgentEventEntity
    from swiss_ai_hub.core.persistence.messaging.entities.persisted_process_event_entity import PersistedProcessEventEntity
    from swiss_ai_hub.core.persistence.process.process_class_entity import ProgramInSpecsEntity
    from swiss_ai_hub.core.persistence.messaging.entities.persisted_agent_event_entity import Resolution
    from swiss_ai_hub.core.persistence.messaging.entities.thread_entity import ThreadEntity
    from swiss_ai_hub.core.persistence.messaging.entities.persisted_agent_event_entity import TimeRange
    from swiss_ai_hub.core.persistence.access.entities.role_entity import UsageLimit
    from swiss_ai_hub.core.persistence.messaging.entities.thread_entity import User
    from swiss_ai_hub.core.persistence.user.user_entity import UserEntity
        PersistedAgentEventEntity,
        Resolution,
        TimeRange,
    )
    from swiss_ai_hub.core.persistence.messaging.entities.persisted_process_event_entity import (
        PersistedProcessEventEntity,
    )
    from swiss_ai_hub.core.persistence.messaging.entities.thread_entity import AgentInstanceRef, ThreadEntity, User
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
    from swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_vector_store_config import MilvusVectorStoreConfig
    from swiss_ai_hub.core.persistence.user.user_entity import Dashboard, DashboardItem, UserEntity
    from swiss_ai_hub.core.persistence.utils import str_to_object_id

__all__ = [
    "get_partition_name_for_namespace",
    "create_milvus_vector_store",
    "VERSION",
    "UPDATED_AT",
    "TYPE",
    "SOURCE_ORIGIN",
    "SOURCE",
    "SECTION_START_LINE",
    "SECTION_END_LINE",
    "REFERENCE_URL",
    "REFERENCE_NAME",
    "PAGE",
    "NodeTypeValue",
    "NODE_TYPE_SUMMARY",
    "NODE_TYPE_CONTENT",
    "NODE_CONTENT_TYPE_TEXT",
    "NODE_CONTENT_TYPE_FIGURE",
    "NODE_CONTENT_TYPE",
    "NAMESPACE",
    "MilvusIndexType",
    "LANGUAGE",
    "IS_INGESTED",
    "INSERTED_AT",
    "INDEX",
    "HASH",
    "H6",
    "H5",
    "H4",
    "H3",
    "H2",
    "H1",
    "DOCUMENT_TITLE",
    "DOCUMENT_STORE_NAME",
    "DOCUMENT_ID",
    "CREATED_AT",
    "AgentClassEntity",
    "AgentConfigEntityDocument",
    "AgentInSpecsEntity",
    "AgentInstanceRef",
    "BearerToken",
    "BucketEntity",
    "Dashboard",
    "DashboardItem",
    "EventBucket",
    "HumanInSpecsEntity",
    "LocaleStringEntity",
    "MilvusVectorStoreConfig",
    "NamespaceEntity",
    "NotificationEntity",
    "PersistedAgentEventEntity",
    "PersistedProcessEventEntity",
    "ProcessClassEntity",
    "ProcessConfigEntityDocument",
    "ProgramInSpecsEntity",
    "RefDoc",
    "Resolution",
    "RoleEntity",
    "TenantEntity",
    "ThreadEntity",
    "TimeRange",
    "UsageLimit",
    "User",
    "UserEntity",
    "UserTenantRoleEntity",
    "VectorStoreFactory",
    "create_mongo_document_store",
    "str_to_object_id",
]

_LAZY_IMPORTS = {
    "get_partition_name_for_namespace": "swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_partition_manager",
    "create_milvus_vector_store": "swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_vector_store_factory",
    "VERSION": "swiss_ai_hub.core.persistence.rag.vectors.node_metadata",
    "UPDATED_AT": "swiss_ai_hub.core.persistence.rag.vectors.node_metadata",
    "TYPE": "swiss_ai_hub.core.persistence.rag.vectors.node_metadata",
    "SOURCE_ORIGIN": "swiss_ai_hub.core.persistence.rag.vectors.node_metadata",
    "SOURCE": "swiss_ai_hub.core.persistence.rag.vectors.node_metadata",
    "SECTION_START_LINE": "swiss_ai_hub.core.persistence.rag.vectors.node_metadata",
    "SECTION_END_LINE": "swiss_ai_hub.core.persistence.rag.vectors.node_metadata",
    "REFERENCE_URL": "swiss_ai_hub.core.persistence.rag.vectors.node_metadata",
    "REFERENCE_NAME": "swiss_ai_hub.core.persistence.rag.vectors.node_metadata",
    "PAGE": "swiss_ai_hub.core.persistence.rag.vectors.node_metadata",
    "NodeTypeValue": "swiss_ai_hub.core.persistence.rag.vectors.node_metadata",
    "NODE_TYPE_SUMMARY": "swiss_ai_hub.core.persistence.rag.vectors.node_metadata",
    "NODE_TYPE_CONTENT": "swiss_ai_hub.core.persistence.rag.vectors.node_metadata",
    "NODE_CONTENT_TYPE_TEXT": "swiss_ai_hub.core.persistence.rag.vectors.node_metadata",
    "NODE_CONTENT_TYPE_FIGURE": "swiss_ai_hub.core.persistence.rag.vectors.node_metadata",
    "NODE_CONTENT_TYPE": "swiss_ai_hub.core.persistence.rag.vectors.node_metadata",
    "NAMESPACE": "swiss_ai_hub.core.persistence.rag.vectors.node_metadata",
    "MilvusIndexType": "swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_vector_store_factory",
    "LANGUAGE": "swiss_ai_hub.core.persistence.rag.vectors.node_metadata",
    "IS_INGESTED": "swiss_ai_hub.core.persistence.rag.vectors.node_metadata",
    "INSERTED_AT": "swiss_ai_hub.core.persistence.rag.vectors.node_metadata",
    "INDEX": "swiss_ai_hub.core.persistence.rag.vectors.node_metadata",
    "HASH": "swiss_ai_hub.core.persistence.rag.vectors.node_metadata",
    "H6": "swiss_ai_hub.core.persistence.rag.vectors.node_metadata",
    "H5": "swiss_ai_hub.core.persistence.rag.vectors.node_metadata",
    "H4": "swiss_ai_hub.core.persistence.rag.vectors.node_metadata",
    "H3": "swiss_ai_hub.core.persistence.rag.vectors.node_metadata",
    "H2": "swiss_ai_hub.core.persistence.rag.vectors.node_metadata",
    "H1": "swiss_ai_hub.core.persistence.rag.vectors.node_metadata",
    "DOCUMENT_TITLE": "swiss_ai_hub.core.persistence.rag.vectors.node_metadata",
    "DOCUMENT_STORE_NAME": "swiss_ai_hub.core.persistence.rag.vectors.node_metadata",
    "DOCUMENT_ID": "swiss_ai_hub.core.persistence.rag.vectors.node_metadata",
    "CREATED_AT": "swiss_ai_hub.core.persistence.rag.vectors.node_metadata",
    "AgentClassEntity": "swiss_ai_hub.core.persistence.agents.agent_class_entity",
    "AgentConfigEntityDocument": "swiss_ai_hub.core.persistence.agents.agent_config_entity_document",
    "AgentInSpecsEntity": "swiss_ai_hub.core.persistence.process.process_class_entity",
    "AgentInstanceRef": "swiss_ai_hub.core.persistence.messaging.entities.thread_entity",
    "BearerToken": "swiss_ai_hub.core.persistence.access.entities.bearer_token",
    "BucketEntity": "swiss_ai_hub.core.persistence.rag.datalake.entities.bucket_entity",
    "Dashboard": "swiss_ai_hub.core.persistence.user.user_entity",
    "DashboardItem": "swiss_ai_hub.core.persistence.user.user_entity",
    "EventBucket": "swiss_ai_hub.core.persistence.messaging.entities.types.event_bucket",
    "HumanInSpecsEntity": "swiss_ai_hub.core.persistence.process.process_class_entity",
    "LocaleStringEntity": "swiss_ai_hub.core.persistence.i18n.locale_string_entity",
    "MilvusVectorStoreConfig": "swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_vector_store_config",
    "NamespaceEntity": "swiss_ai_hub.core.persistence.rag.datalake.entities.namespace_entity",
    "NotificationEntity": "swiss_ai_hub.core.persistence.notification.notification_entity",
    "PersistedAgentEventEntity": "swiss_ai_hub.core.persistence.messaging.entities.persisted_agent_event_entity",
    "PersistedProcessEventEntity": "swiss_ai_hub.core.persistence.messaging.entities.persisted_process_event_entity",
    "ProcessClassEntity": "swiss_ai_hub.core.persistence.process.process_class_entity",
    "ProcessConfigEntityDocument": "swiss_ai_hub.core.persistence.process.process_config_entity_document",
    "ProgramInSpecsEntity": "swiss_ai_hub.core.persistence.process.process_class_entity",
    "RefDoc": "swiss_ai_hub.core.persistence.rag.documents.entities.ref_doc",
    "Resolution": "swiss_ai_hub.core.persistence.messaging.entities.persisted_agent_event_entity",
    "RoleEntity": "swiss_ai_hub.core.persistence.access.entities.role_entity",
    "TenantEntity": "swiss_ai_hub.core.persistence.access.entities.tenant_entity",
    "ThreadEntity": "swiss_ai_hub.core.persistence.messaging.entities.thread_entity",
    "TimeRange": "swiss_ai_hub.core.persistence.messaging.entities.persisted_agent_event_entity",
    "UsageLimit": "swiss_ai_hub.core.persistence.access.entities.role_entity",
    "User": "swiss_ai_hub.core.persistence.messaging.entities.thread_entity",
    "UserEntity": "swiss_ai_hub.core.persistence.user.user_entity",
    "UserTenantRoleEntity": "swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity",
    "VectorStoreFactory": "swiss_ai_hub.core.persistence.rag.vectors",
    "create_mongo_document_store": "swiss_ai_hub.core.persistence.rag.documents.stores.docstore",
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
