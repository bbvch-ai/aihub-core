from aihub_lib.nats.events import RetrieverEvent
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

from aihub_agent.agents.rag.RetrieverStepConfig import RetrieverStepConfig


def retriever_step(config: RetrieverStepConfig, message: str) -> RetrieverEvent:
    storage_context = StorageContext.from_defaults(
        vector_store=create_azure_ai_search_vector_store(config.index_name),
        docstore=create_mongo_document_store(config.index_name),
    )
    index = VectorStoreIndex.from_vector_store(
        storage_context.vector_store,
        embed_model=config.embed_model,
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
            for ns in config.index_namespaces
            for nt in config.node_types
        ],
        condition="or",
    )

    retriever = VectorIndexRetriever(
        vector_store_query_mode=config.query_mode,
        index=index,
        similarity_top_k=config.retrieve_k,
        filters=filters,
    )

    nodes = retriever.retrieve(message)

    if config.query_mode == VectorStoreQueryMode.SEMANTIC_HYBRID:
        nodes = ScoreScalerPostprocessor(from_min=0, from_max=4).process(nodes)
    return RetrieverEvent(documents=nodes)
