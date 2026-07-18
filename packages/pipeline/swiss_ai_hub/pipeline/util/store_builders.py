import asyncio
from functools import cache

import boto3
from llama_index.storage.docstore.mongodb import MongoDocumentStore
from llama_index.vector_stores.milvus import MilvusVectorStore
from pymilvus import MilvusClient
from swiss_ai_hub.core.generative_ai.document.accessor.s3_anonymous_file_access_service import (
    S3AnonymousFileAccessService,
)
from swiss_ai_hub.core.infrastructure import MilvusSettings, S3StorageSettings
from swiss_ai_hub.core.persistence.rag.documents.stores.docstore import create_mongo_document_store
from swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_vector_store_factory import (
    MilvusIndexType,
    create_milvus_vector_store,
)

from swiss_ai_hub.pipeline.resources.data_lake.s3.s3_data_lake_client import S3DataLakeClient

"""Per-bucket store builders for the RAG pipeline.

The RAG pipeline ingests every self-service knowledge database from a single deployed code
location, so it cannot bake a store/collection name into resources at ``Definitions``-build time. Instead
it resolves the target store per run — from the composite partition key on the partitioned write path, or
from the ``aihub/bucket`` run tag on the non-partitioned observe/remove path — and builds the store here.
Builds are cached per identity so repeated lookups within a process reuse a single connection.
"""

# Lazily-created, process-wide event loop for building vector stores from a synchronous caller.
# pymilvus 2.6+ constructs an AsyncMilvusClient in MilvusVectorStore.__init__ (which calls
# asyncio.get_running_loop()) and retains a reference to that loop for the store's lifetime, so it
# cannot be closed. Sharing one loop across every bucket keeps this to a single long-lived loop for the
# whole process rather than one per store_name (which also avoids N "unclosed event loop" warnings).
_vector_store_loop: asyncio.AbstractEventLoop | None = None


@cache
def build_doc_store(store_name: str) -> MongoDocumentStore:
    """Mongo document store for a knowledge database. ``create_mongo_document_store`` is itself cached."""
    return create_mongo_document_store(store_name)


@cache
def build_vector_store(store_name: str) -> MilvusVectorStore:
    """Milvus vector store for a knowledge database's collection.

    Mirrors ``MilvusVectorStoreResource``: pymilvus 2.6+ builds an ``AsyncMilvusClient`` during
    ``MilvusVectorStore`` init which calls ``asyncio.get_running_loop()``, so a running loop must exist.
    """
    milvus_settings = MilvusSettings()
    client = MilvusClient(uri=milvus_settings.URL, token=milvus_settings.get_token())

    def _create() -> MilvusVectorStore:
        return create_milvus_vector_store(
            client=client,
            collection_name=store_name,
            embedding_vector_dimension=milvus_settings.DIMENSION,
            index_type=MilvusIndexType.HNSW,
            uri=milvus_settings.URL,
            token=milvus_settings.get_token(),
        )

    try:
        asyncio.get_running_loop()
        return _create()
    except RuntimeError:
        global _vector_store_loop
        if _vector_store_loop is None:
            _vector_store_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(_vector_store_loop)

        async def _async_create() -> MilvusVectorStore:  # noqa: S7503
            return _create()

        return _vector_store_loop.run_until_complete(_async_create())


def build_s3_data_lake_client(bucket: str, *, ensure_bucket: bool = False) -> S3DataLakeClient:
    """S3 data lake client scoped to ``bucket``.

    The read path passes ``ensure_bucket=False`` (the bucket already exists by the time documents are
    processed); the observe path provisions a brand-new bucket on first ingest.
    """
    s3_config = S3StorageSettings()
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=s3_config.ACCESS_KEY,
        aws_secret_access_key=s3_config.SECRET_KEY.get_secret_value(),
        region_name=s3_config.REGION,
        endpoint_url=s3_config.ENDPOINT,
    )
    return S3DataLakeClient(bucket, s3_client, ensure_bucket=ensure_bucket)


@cache
def build_s3_file_access_service() -> S3AnonymousFileAccessService:
    """Core S3 service used by knowledge teardown for ``delete_prefix`` / ``delete_container``.

    Teardown only ever deletes objects, so it needs just the internal client; the same client is passed
    as the public one because no presigned URLs are generated here.
    """
    s3_config = S3StorageSettings()
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=s3_config.ACCESS_KEY,
        aws_secret_access_key=s3_config.SECRET_KEY.get_secret_value(),
        region_name=s3_config.REGION,
        endpoint_url=s3_config.ENDPOINT,
    )
    return S3AnonymousFileAccessService(s3_client=s3_client, s3_public_client=s3_client, s3_settings=s3_config)
