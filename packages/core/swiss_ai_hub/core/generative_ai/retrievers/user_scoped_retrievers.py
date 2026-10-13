import asyncio
from collections.abc import Callable

from mongoengine import DoesNotExist

from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.generative_ai.retrievers.retrieval_runtime_config import RetrievalRuntimeConfig
from swiss_ai_hub.core.persistence.rag.datalake.entities.bucket_entity import BucketEntity
from swiss_ai_hub.core.persistence.rag.datalake.entities.namespace_entity import NamespaceEntity


class UserScopedRetrievers:
    """Narrows a run's retrievers to the collections the asking user may read, by the rules the knowledge UI uses.

    A profile is checked once, against whoever saved it, so a user with narrower access would otherwise get
    answers from collections they cannot open. A retriever reading a whole database stays whole only for a user
    who may read all of it; for anyone else it falls back to the namespaces they may read, which is why the
    database's current namespaces are looked up.
    """

    @staticmethod
    async def narrow(
        runtime_configs: list[RetrievalRuntimeConfig], access_checker: AccessChecker
    ) -> list[RetrievalRuntimeConfig]:
        return await asyncio.to_thread(
            UserScopedRetrievers.restrict, runtime_configs, access_checker, UserScopedRetrievers.namespaces_of
        )

    @staticmethod
    def restrict(
        runtime_configs: list[RetrievalRuntimeConfig],
        access_checker: AccessChecker,
        namespaces_of: Callable[[str], list[str]],
    ) -> list[RetrievalRuntimeConfig]:
        restricted = []
        for runtime_config in runtime_configs:
            vector_store = runtime_config.config.vector_store
            database = vector_store.collection_name
            if vector_store.all_namespaces and access_checker.has_access_to_all_knowledge_namespaces(database):
                restricted.append(runtime_config)
                continue
            candidates = namespaces_of(database) if vector_store.all_namespaces else vector_store.index_namespaces
            readable = [
                namespace
                for namespace in candidates
                if access_checker.has_access_to_knowledge_namespace(database, namespace)
            ]
            if not readable:
                continue
            if readable == vector_store.index_namespaces:
                restricted.append(runtime_config)
                continue
            narrowed_store = vector_store.model_copy(update={"index_namespaces": readable, "all_namespaces": False})
            narrowed_config = runtime_config.config.model_copy(update={"vector_store": narrowed_store})
            restricted.append(runtime_config.model_copy(update={"config": narrowed_config}))
        return restricted

    @staticmethod
    def readable_namespaces(
        access_checker: AccessChecker, namespaces_by_database: dict[str, list[str]]
    ) -> dict[str, list[str]]:
        """The namespaces the user may open, by database; a database left with none is dropped."""
        readable = {
            database: [ns for ns in namespaces if access_checker.has_access_to_knowledge_namespace(database, ns)]
            for database, namespaces in namespaces_by_database.items()
        }
        return {database: namespaces for database, namespaces in readable.items() if namespaces}

    @staticmethod
    def namespaces_of(database: str) -> list[str]:
        """The database's live namespaces; one being torn down is no longer offered to anyone."""
        try:
            bucket = BucketEntity.get_bucket_by_db_name(database)
        except DoesNotExist:
            return []
        return [
            namespace.namespace_name
            for namespace in NamespaceEntity.get_namespaces_by_bucket(str(bucket.id))
            if not namespace.deleting
        ]
