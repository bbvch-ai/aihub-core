from typing import Annotated, ClassVar

from llama_index.vector_stores.milvus import IndexManagement
from llama_index.vector_stores.milvus.utils import BM25BuiltInFunction
from pymilvus import MilvusClient

from swiss_ai_hub.core.infrastructure.milvus.milvus_settings import MilvusSettings
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import DOCUMENT_ID
from swiss_ai_hub.core.persistence.rag.vectors.stores.partition_aware_milvus_vector_store import (
    PartitionAwareMilvusVectorStore,
)


class ExistingMilvusVectorStores:
    """Stores for reading collections that already exist: never one that creates a collection, built once each.

    `create_milvus_vector_store` and llama-index's `MilvusVectorStore` both create a missing collection with its 1,023
    partitions, which a read must never do: a knowledge database without a collection simply has no vectors yet.
    Building a store also opens clients and lists indexes, so each is built once per process on one shared client and
    reused. The index check is skipped and the async client left out, since a read creates no index and pymilvus binds
    an async client to the event loop running at construction, which a worker thread does not have. Two threads
    building the same store at once is harmless: the later one replaces the earlier.
    """

    _client: ClassVar[MilvusClient | None] = None
    _stores: ClassVar[dict[str, PartitionAwareMilvusVectorStore]] = {}

    @classmethod
    def find(
        cls, collection_name: Annotated[str, "The knowledge database's Milvus collection"]
    ) -> PartitionAwareMilvusVectorStore | None:
        """The collection's store, or None when the collection does not exist (or no longer does)."""
        client = cls._shared_client()
        if not client.has_collection(collection_name):
            cls._stores.pop(collection_name, None)
            return None
        if collection_name not in cls._stores:
            cls._stores[collection_name] = cls._build(client, collection_name)
        return cls._stores[collection_name]

    @classmethod
    def _shared_client(cls) -> MilvusClient:
        if cls._client is None:
            settings = MilvusSettings()
            cls._client = MilvusClient(uri=settings.URL, token=settings.get_token())
        return cls._client

    @staticmethod
    def _build(client: MilvusClient, collection_name: str) -> PartitionAwareMilvusVectorStore:
        """Built with the arguments `create_milvus_vector_store` uses, so reads see the fields the pipeline wrote."""
        settings = MilvusSettings()
        return PartitionAwareMilvusVectorStore(
            client=client,
            uri=settings.URL,
            token=settings.get_token(),
            collection_name=collection_name,
            dim=settings.DIMENSION,
            overwrite=False,
            doc_id_field=DOCUMENT_ID,
            enable_sparse=True,
            sparse_embedding_function=BM25BuiltInFunction(),
            upsert_mode=True,
            index_management=IndexManagement.NO_VALIDATION,
            use_async_client=False,
        )
