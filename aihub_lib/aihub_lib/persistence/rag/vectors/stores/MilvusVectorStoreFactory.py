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


class MilvusIndexType(str, Enum):
    """
    Vector index types for RAG workloads.

    Memory per vector (3072-dim embeddings): ~12.4 KB (12 KB data + 64 bytes graph)
    Partitioning divides load: 1M vectors / 1000 namespaces = 1K vectors per partition queried

    Scale guide:
    - <1M vectors (12 GB): HNSW (fastest, use mmap if memory tight)
    - 1-10M vectors (120 GB): HNSW + mmap or DISKANN (if <10 GB RAM available)
    - >10M vectors: DISKANN only (requires NVMe SSD)
    """

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
    index_type: MilvusIndexType = MilvusIndexType.HNSW,
    enable_mmap: bool = True,  # Enabled by default: reduces RAM by 50-70% (disable if latency variance unacceptable)
    num_partitions: Annotated[
        int, Field(ge=1, le=1023, description="Hash partitions for distributing namespaces across physical storage")
    ] = 1023,
) -> MilvusVectorStore:
    """
    Factory for namespace-partitioned vector stores optimized for RAG workloads.

    Design for RAG:
    - Partition key on namespace: Queries only search relevant namespaces (departments, projects)
    - Hybrid search: Dense (semantic) + BM25 (keyword) for comprehensive retrieval
    - HNSW index default: Best recall/speed for semantic search (97-99% accuracy, 10-100x faster than exact)
    - Memory-mapped I/O: Optional mmap reduces RAM usage by offloading to disk (OS page cache)

    Index selection:
    - HNSW (default): Best for RAG quality, enable mmap if memory constrained
    - DISKANN: Use when vectors exceed available RAM (requires NVMe SSD)
    - IVF_FLAT: Middle ground if HNSW too memory-intensive and DISKANN unavailable

    Memory math (3072-dim): ~12.4 KB/vector (12 KB embeddings + 64 bytes HNSW graph)
    - 100K vectors: 1.2 GB RAM (HNSW) or ~100 MB RAM (DISKANN)
    - 1M vectors: 12 GB RAM (HNSW) or ~1 GB RAM (DISKANN)
    - 10M vectors: 121 GB RAM (HNSW) or ~10 GB RAM (DISKANN)
    """
    client = MilvusClient(uri=uri)
    if not client.has_collection(collection_name):
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, auto_id=False, max_length=255),
            FieldSchema(name=DOCUMENT_ID, dtype=DataType.VARCHAR, max_length=255),
            FieldSchema(name=NAMESPACE, dtype=DataType.VARCHAR, max_length=255, is_partition_key=True),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=embedding_vector_dimension),
            FieldSchema(name="sparse_embedding", dtype=DataType.SPARSE_FLOAT_VECTOR),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535, enable_analyzer=True),
            FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=65535),
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
                params={
                    "M": 16,  # Links per node: higher = better recall, more memory (8-64 range)
                    "efConstruction": 200,  # Build quality: higher = better recall, slower build (64-512 range)
                },
            )
        elif index_type == MilvusIndexType.IVF_FLAT:
            index_params.add_index(
                field_name="embedding",
                index_type="IVF_FLAT",
                metric_type="IP",
                params={"nlist": 1024},  # Clusters: sqrt(N) typically optimal
            )
        elif index_type == MilvusIndexType.FLAT:
            index_params.add_index(field_name="embedding", index_type="FLAT", metric_type="IP")
        elif index_type == MilvusIndexType.DISKANN:
            index_params.add_index(field_name="embedding", index_type="DISKANN", metric_type="IP")

        index_params.add_index(field_name="sparse_embedding", index_type="SPARSE_INVERTED_INDEX", metric_type="BM25")

        client.create_collection(
            collection_name=collection_name, schema=schema, index_params=index_params, num_partitions=num_partitions
        )

        if enable_mmap:
            _enable_mmap(uri, collection_name)

    return MilvusVectorStore(
        uri=uri,
        collection_name=collection_name,
        dim=embedding_vector_dimension,
        overwrite=False,
        doc_id_field=DOCUMENT_ID,
        enable_sparse=True,
        sparse_embedding_function=BM25BuiltInFunction(),
    )


def _enable_mmap(uri: str, collection_name: str) -> None:
    """
    Enable memory-mapped I/O to reduce RAM usage.

    Offloads vector data to disk via OS page cache. Reduces memory footprint by 50-70%
    with minimal performance impact (relies on fast disk I/O and OS caching).

    Best for: HNSW indexes when memory constrained but disk is fast (SSD).
    Not needed: DISKANN already uses disk storage.
    """
    connections.connect(uri=uri)
    collection = Collection(name=collection_name)
    collection.set_properties({"mmap.enabled": True})
