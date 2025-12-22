from enum import Enum
from functools import cache
from typing import Annotated

from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.vector_stores.milvus.utils import BM25BuiltInFunction
from pydantic import Field, validate_call
from pymilvus import (
    CollectionSchema,
    DataType,
    FieldSchema,
    Function,
    FunctionType,
    MilvusClient,
)

from aihub_lib.persistence.rag.vectors.node_metadata import DOCUMENT_ID, NAMESPACE
from aihub_lib.persistence.rag.vectors.stores.MilvusPartitionManager import create_manual_partitions
from aihub_lib.persistence.rag.vectors.stores.PartitionAwareMilvusVectorStore import PartitionAwareMilvusVectorStore


class MilvusIndexType(str, Enum):
    HNSW = "HNSW"  # RAG optimal: 97-99% recall, fastest queries, highest memory (enable mmap to reduce)
    DISKANN = "DISKANN"  # Memory-constrained: 90-95% recall, 90% less RAM, requires NVMe SSD
    IVF_FLAT = "IVF_FLAT"  # Balanced: 95-98% recall, 50% less memory than HNSW
    FLAT = "FLAT"  # Dev/test only: 100% recall, no production scaling


@cache
@validate_call
def create_milvus_vector_store(
    uri: Annotated[str, Field(description="Milvus connection URI")],
    collection_name: Annotated[str, Field(description="Name of the collection to create or use")],
    embedding_vector_dimension: Annotated[int, Field(gt=0, description="Dimension of dense embedding vectors")],
    index_type: Annotated[MilvusIndexType, Field(description="Vector index type for the embedding field")] = (
        MilvusIndexType.HNSW
    ),
    token: Annotated[str | None, Field(description="Authentication token in format 'username:password'")] = None,
) -> MilvusVectorStore:
    """
    Factory for namespace-partitioned vector stores optimized for RAG workloads.

    - Manual partition by namespace: Queries only load relevant namespaces
    - Hybrid search: Dense (semantic) + BM25 (keyword) for comprehensive retrieval
    - HNSW index default: Best recall/speed for semantic search

    Index selection:
    - HNSW (default): Best for RAG quality, enable mmap if memory constrained
    - DISKANN: Use when vectors exceed available RAM (requires NVMe SSD)
    - IVF_FLAT: Middle ground if HNSW too memory-intensive and DISKANN unavailable
    """
    client = MilvusClient(uri=uri, token=token)
    if not client.has_collection(collection_name):
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, auto_id=False, max_length=255),
            FieldSchema(name=DOCUMENT_ID, dtype=DataType.VARCHAR, max_length=255),
            FieldSchema(name=NAMESPACE, dtype=DataType.VARCHAR, max_length=255),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=embedding_vector_dimension),
            FieldSchema(name="sparse_embedding", dtype=DataType.SPARSE_FLOAT_VECTOR),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535, enable_analyzer=True),
        ]
        schema = CollectionSchema(fields=fields, enable_dynamic_field=True)

        bm25_function = Function(
            name="bm25_fn",
            function_type=FunctionType.BM25,
            input_field_names=["text"],
            output_field_names=["sparse_embedding"],
            params={},
        )
        schema.add_function(bm25_function)

        index_params = client.prepare_index_params()

        if index_type == MilvusIndexType.HNSW:
            index_params.add_index(
                field_name="embedding",
                index_type="HNSW",
                metric_type="IP",
            )
        elif index_type == MilvusIndexType.IVF_FLAT:
            index_params.add_index(
                field_name="embedding",
                index_type="IVF_FLAT",
                metric_type="IP",
            )
        elif index_type == MilvusIndexType.FLAT:
            index_params.add_index(
                field_name="embedding",
                index_type="FLAT",
                metric_type="IP",
            )
        elif index_type == MilvusIndexType.DISKANN:
            index_params.add_index(field_name="embedding", index_type="DISKANN", metric_type="IP")

        index_params.add_index(field_name="sparse_embedding", index_type="SPARSE_INVERTED_INDEX", metric_type="BM25")

        client.create_collection(collection_name=collection_name, schema=schema, index_params=index_params)

        create_manual_partitions(client=client, collection_name=collection_name)

    return PartitionAwareMilvusVectorStore(
        uri=uri,
        token=token,
        collection_name=collection_name,
        dim=embedding_vector_dimension,
        overwrite=False,
        doc_id_field=DOCUMENT_ID,
        enable_sparse=True,
        sparse_embedding_function=BM25BuiltInFunction(),
        upsert_mode=True,
    )
