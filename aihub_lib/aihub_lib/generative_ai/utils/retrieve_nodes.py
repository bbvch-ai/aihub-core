from typing import List, Optional

from aihub_lib.nats.events.semantic.retriever import Document
from aihub_lib.persistence.rag.documents.stores.MongoDocumentStoreFactory import (
    create_mongo_document_store,
)
from aihub_lib.persistence.rag.vectors.node_metadata import (
    NAMESPACE,
    TYPE,
)
from aihub_lib.persistence.rag.vectors.stores.AzureAISearchVectorStoreFactory import (
    create_azure_ai_search_vector_store,
)
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.core.indices.vector_store import VectorIndexRetriever
from llama_index.core.vector_stores import MetadataFilters, MetadataFilter
from llama_index.core.vector_stores.types import VectorStoreQueryMode


def retrieve_nodes(
    message: str,
    embed_model,
    index_name: str,
    index_namespaces: List[str],
    query_mode: VectorStoreQueryMode,
    node_types: List[str],
    retrieve_k: int,
) -> Optional[List[Document]]:
    storage_context = StorageContext.from_defaults(
        vector_store=create_azure_ai_search_vector_store(index_name),
        docstore=create_mongo_document_store(index_name),
    )
    index = VectorStoreIndex.from_vector_store(
        storage_context.vector_store,
        embed_model=embed_model,
        storage_context=storage_context,
    )
    filters = MetadataFilters(
        filters=[
            MetadataFilters(
                filters=[
                    MetadataFilter(key=NAMESPACE, value=ns),
                    MetadataFilter(key=TYPE, value=nt),
                ],
                condition="and",
            )
            for ns in index_namespaces
            for nt in node_types
        ],
        condition="or",
    )
    retriever = VectorIndexRetriever(
        vector_store_query_mode=query_mode,
        index=index,
        similarity_top_k=retrieve_k,
        filters=filters,
    )
    nodes = retriever.retrieve(message)
    if query_mode == VectorStoreQueryMode.SEMANTIC_HYBRID:
        nodes = ScoreScalerPostprocessor(from_min=0, from_max=4).process(nodes)
    return nodes
