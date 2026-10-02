from collections.abc import Callable

from mongoengine import DoesNotExist

from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.events.agent.user.knowledge_reference import KnowledgeReference
from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_model_config import EmbeddingModelConfig
from swiss_ai_hub.core.generative_ai.retrievers.knowledge_retriever_config import KnowledgeRetrieverConfig
from swiss_ai_hub.core.generative_ai.retrievers.retrieval_runtime_config import RetrievalRuntimeConfig
from swiss_ai_hub.core.generative_ai.retrievers.user_scoped_retrievers import UserScopedRetrievers
from swiss_ai_hub.core.infrastructure.document_ingestion_pipeline.document_ingestion_pipeline_settings import (
    DocumentIngestionPipelineSettings,
)
from swiss_ai_hub.core.persistence.rag.datalake.entities.bucket_entity import BucketEntity
from swiss_ai_hub.core.persistence.rag.datalake.knowledge_visibility import KnowledgeVisibility
from swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_vector_store_config import MilvusVectorStoreConfig


class ReferencedKnowledge:
    """Retrievers for collections a user referenced at runtime, rather than ones a profile configured.

    Nothing about such a collection is known up front, so each database is searched with the embedding model it was
    indexed with: vectors are only comparable to vectors from the same model.
    """

    @staticmethod
    def partition(
        references: list[KnowledgeReference],
        access_checker: AccessChecker | None,
        namespaces_of: Callable[[str], list[str]],
    ) -> tuple[list[KnowledgeReference], list[KnowledgeReference]]:
        """The references to search, and those refused: a collection that is gone, or one the user may not read.

        A run without a user was started by the platform, whose references are its own to make.
        """
        unique = list(dict.fromkeys((reference.database, reference.namespace) for reference in references))
        live = {database: set(namespaces_of(database)) for database in {database for database, _ in unique}}
        searchable, refused = [], []
        for database, namespace in unique:
            reference = KnowledgeReference(database=database, namespace=namespace)
            readable = access_checker is None or access_checker.has_access_to_knowledge_namespace(database, namespace)
            (searchable if namespace in live[database] and readable else refused).append(reference)
        return searchable, refused

    @staticmethod
    def namespaces_of(database: str) -> list[str]:
        """The collections a user may reference in the database: its live ones, none when the platform hides it.

        A reference arrives from a chat client, so a hidden database must not become reachable by naming it there.
        """
        if not KnowledgeVisibility.is_browsable_database(database):
            return []
        return UserScopedRetrievers.namespaces_of(database)

    @staticmethod
    def retrievers(references: list[KnowledgeReference], retrieve_k: int) -> list[RetrievalRuntimeConfig]:
        """One retriever per database, over the referenced collections in it."""
        namespaces_by_database: dict[str, list[str]] = {}
        for reference in references:
            namespaces_by_database.setdefault(reference.database, []).append(reference.namespace)
        return [
            RetrievalRuntimeConfig.from_config(
                KnowledgeRetrieverConfig(
                    embed_model=EmbeddingModelConfig(model_name=ReferencedKnowledge.embedding_model_of(database)),
                    vector_store=MilvusVectorStoreConfig(collection_name=database, index_namespaces=namespaces),
                    retrieve_k=retrieve_k,
                )
            )
            for database, namespaces in namespaces_by_database.items()
        ]

    @staticmethod
    def embedding_model_of(database: str) -> str:
        """The model the database is indexed with; one created before the choice existed uses the default."""
        try:
            configuration = BucketEntity.get_bucket_by_db_name(database).configuration or {}
        except DoesNotExist:
            configuration = {}
        return configuration.get("embedding_model") or DocumentIngestionPipelineSettings().EMBEDDING_MODEL
