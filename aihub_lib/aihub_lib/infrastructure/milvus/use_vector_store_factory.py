from fastapi import Request
from pymilvus import MilvusClient

from aihub_lib.infrastructure.milvus.MilvusSettings import MilvusSettings
from aihub_lib.persistence.rag.vectors import VectorStoreFactory
from aihub_lib.persistence.rag.vectors.stores.MilvusVectorStoreFactory import create_milvus_vector_store


def use_vector_store_factory(request: Request) -> VectorStoreFactory:
    """
    FastAPI dependency that provides a vector store factory using the shared Milvus client.

    The factory creates collection-specific vector stores while reusing the same
    underlying Milvus connection for health checks and connection pooling.
    """
    milvus_client: MilvusClient = request.app.state.milvus_client
    dimension = MilvusSettings().DIMENSION

    def factory(collection: str):
        return create_milvus_vector_store(
            client=milvus_client,
            collection_name=collection,
            embedding_vector_dimension=dimension,
        )

    return factory
