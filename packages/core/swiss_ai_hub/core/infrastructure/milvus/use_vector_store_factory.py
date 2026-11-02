from fastapi import Request
from pymilvus import MilvusClient

from swiss_ai_hub.core.infrastructure.milvus.milvus_settings import MilvusSettings
from swiss_ai_hub.core.infrastructure.milvus.use_milvus import use_milvus
from swiss_ai_hub.core.persistence.rag.vectors import VectorStoreFactory
from swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_vector_store_factory import create_milvus_vector_store


def use_vector_store_factory(request: Request) -> VectorStoreFactory:
    """
    FastAPI dependency that provides a vector store factory using the shared Milvus client.

    The factory creates collection-specific vector stores while reusing the same
    underlying Milvus connection for health checks and connection pooling.
    """
    milvus_client: MilvusClient = use_milvus(request)
    settings = MilvusSettings()

    def factory(collection: str):
        return create_milvus_vector_store(
            client=milvus_client,
            collection_name=collection,
            embedding_vector_dimension=settings.DIMENSION,
            uri=settings.URL,
            token=settings.get_token(),
        )

    return factory
