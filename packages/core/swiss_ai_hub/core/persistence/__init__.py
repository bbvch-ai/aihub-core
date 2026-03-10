from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.persistence.access.entities.BearerToken import BearerToken
    from swiss_ai_hub.core.persistence.access.entities.RoleEntity import RoleEntity, UsageLimit
    from swiss_ai_hub.core.persistence.access.entities.TenantEntity import TenantEntity
    from swiss_ai_hub.core.persistence.access.entities.UserTenantRoleEntity import UserTenantRoleEntity
    from swiss_ai_hub.core.persistence.agents.AgentClassEntity import AgentClassEntity
    from swiss_ai_hub.core.persistence.agents.AgentConfigEntityDocument import AgentConfigEntityDocument
    from swiss_ai_hub.core.persistence.i18n.LocaleStringEntity import LocaleStringEntity
    from swiss_ai_hub.core.persistence.messaging.entities.PersistedAgentEventEntity import (
        PersistedAgentEventEntity,
        Resolution,
        TimeRange,
    )
    from swiss_ai_hub.core.persistence.messaging.entities.PersistedProcessEventEntity import (
        PersistedProcessEventEntity,
    )
    from swiss_ai_hub.core.persistence.messaging.entities.ThreadEntity import AgentInstanceRef, ThreadEntity, User
    from swiss_ai_hub.core.persistence.messaging.entities.types.EventBucket import EventBucket
    from swiss_ai_hub.core.persistence.notification.NotificationEntity import NotificationEntity
    from swiss_ai_hub.core.persistence.process.ProcessClassEntity import (
        AgentInSpecsEntity,
        HumanInSpecsEntity,
        ProcessClassEntity,
        ProgramInSpecsEntity,
    )
    from swiss_ai_hub.core.persistence.process.ProcessConfigEntityDocument import ProcessConfigEntityDocument
    from swiss_ai_hub.core.persistence.rag.datalake.entities.BucketEntity import BucketEntity
    from swiss_ai_hub.core.persistence.rag.datalake.entities.NamespaceEntity import NamespaceEntity
    from swiss_ai_hub.core.persistence.rag.documents.entities.RefDoc import RefDoc
    from swiss_ai_hub.core.persistence.rag.documents.stores.docstore import create_mongo_document_store
    from swiss_ai_hub.core.persistence.rag.vectors import VectorStoreFactory
    from swiss_ai_hub.core.persistence.rag.vectors.stores.MilvusVectorStoreConfig import MilvusVectorStoreConfig
    from swiss_ai_hub.core.persistence.user.UserEntity import Dashboard, DashboardItem, UserEntity
    from swiss_ai_hub.core.persistence.utils import str_to_object_id

__all__ = [
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
    "AgentClassEntity": "swiss_ai_hub.core.persistence.agents.AgentClassEntity",
    "AgentConfigEntityDocument": "swiss_ai_hub.core.persistence.agents.AgentConfigEntityDocument",
    "AgentInSpecsEntity": "swiss_ai_hub.core.persistence.process.ProcessClassEntity",
    "AgentInstanceRef": "swiss_ai_hub.core.persistence.messaging.entities.ThreadEntity",
    "BearerToken": "swiss_ai_hub.core.persistence.access.entities.BearerToken",
    "BucketEntity": "swiss_ai_hub.core.persistence.rag.datalake.entities.BucketEntity",
    "Dashboard": "swiss_ai_hub.core.persistence.user.UserEntity",
    "DashboardItem": "swiss_ai_hub.core.persistence.user.UserEntity",
    "EventBucket": "swiss_ai_hub.core.persistence.messaging.entities.types.EventBucket",
    "HumanInSpecsEntity": "swiss_ai_hub.core.persistence.process.ProcessClassEntity",
    "LocaleStringEntity": "swiss_ai_hub.core.persistence.i18n.LocaleStringEntity",
    "MilvusVectorStoreConfig": "swiss_ai_hub.core.persistence.rag.vectors.stores.MilvusVectorStoreConfig",
    "NamespaceEntity": "swiss_ai_hub.core.persistence.rag.datalake.entities.NamespaceEntity",
    "NotificationEntity": "swiss_ai_hub.core.persistence.notification.NotificationEntity",
    "PersistedAgentEventEntity": "swiss_ai_hub.core.persistence.messaging.entities.PersistedAgentEventEntity",
    "PersistedProcessEventEntity": "swiss_ai_hub.core.persistence.messaging.entities.PersistedProcessEventEntity",
    "ProcessClassEntity": "swiss_ai_hub.core.persistence.process.ProcessClassEntity",
    "ProcessConfigEntityDocument": "swiss_ai_hub.core.persistence.process.ProcessConfigEntityDocument",
    "ProgramInSpecsEntity": "swiss_ai_hub.core.persistence.process.ProcessClassEntity",
    "RefDoc": "swiss_ai_hub.core.persistence.rag.documents.entities.RefDoc",
    "Resolution": "swiss_ai_hub.core.persistence.messaging.entities.PersistedAgentEventEntity",
    "RoleEntity": "swiss_ai_hub.core.persistence.access.entities.RoleEntity",
    "TenantEntity": "swiss_ai_hub.core.persistence.access.entities.TenantEntity",
    "ThreadEntity": "swiss_ai_hub.core.persistence.messaging.entities.ThreadEntity",
    "TimeRange": "swiss_ai_hub.core.persistence.messaging.entities.PersistedAgentEventEntity",
    "UsageLimit": "swiss_ai_hub.core.persistence.access.entities.RoleEntity",
    "User": "swiss_ai_hub.core.persistence.messaging.entities.ThreadEntity",
    "UserEntity": "swiss_ai_hub.core.persistence.user.UserEntity",
    "UserTenantRoleEntity": "swiss_ai_hub.core.persistence.access.entities.UserTenantRoleEntity",
    "VectorStoreFactory": "swiss_ai_hub.core.persistence.rag.vectors",
    "create_mongo_document_store": "swiss_ai_hub.core.persistence.rag.documents.stores.docstore",
    "str_to_object_id": "swiss_ai_hub.core.persistence.utils",
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        from importlib import import_module

        return getattr(import_module(_LAZY_IMPORTS[name]), name)
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
