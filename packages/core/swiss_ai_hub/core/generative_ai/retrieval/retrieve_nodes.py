from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.schema import NodeWithScore
from llama_index.core.vector_stores import MetadataFilter
from llama_index.core.vector_stores.types import (
    BasePydanticVectorStore,
    FilterCondition,
    MetadataFilters,
    VectorStoreQuery,
    VectorStoreQueryMode,
)

from swiss_ai_hub.core.generative_ai.processors.min_max_score_normalizer import MinMaxScoreNormalizer
from swiss_ai_hub.core.generative_ai.processors.score_scaler_post_processor import ScoreScalerPostProcessor
from swiss_ai_hub.core.generative_ai.retrievers.metadata_filter_pair import MetadataFilterPair
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import NAMESPACE, TYPE


def retrieve_nodes(
    message: str,
    embed_model: BaseEmbedding,
    retrieve_k: int,
    index_namespaces: list[str],
    query_mode: VectorStoreQueryMode,
    node_types: list[str],
    vector_store: BasePydanticVectorStore,
    additional_filters: list[MetadataFilterPair] | None = None,
) -> list[NodeWithScore] | None:
    if retrieve_k <= 0:
        raise ValueError("retrieve_k must be a positive integer")

    extra_filters = [MetadataFilter(key=f.key, value=f.value) for f in (additional_filters or [])]

    if index_namespaces:
        filters = MetadataFilters(
            filters=[
                MetadataFilters(
                    filters=[
                        MetadataFilter(key=NAMESPACE, value=ns),
                        MetadataFilter(key=TYPE, value=nt),
                        *extra_filters,
                    ],
                    condition=FilterCondition.AND,
                )
                for ns in index_namespaces
                for nt in node_types
            ],
            condition=FilterCondition.OR,
        )
    elif extra_filters:
        filters = MetadataFilters(
            filters=[
                MetadataFilters(
                    filters=[MetadataFilter(key=TYPE, value=nt), *extra_filters],
                    condition=FilterCondition.AND,
                )
                for nt in node_types
            ],
            condition=FilterCondition.OR,
        )
    else:
        filters = MetadataFilters(
            filters=[MetadataFilter(key=TYPE, value=nt) for nt in node_types],
            condition=FilterCondition.OR,
        )

    embedding = embed_model.get_text_embedding(message)

    question_query = vector_store.query(
        VectorStoreQuery(
            query_embedding=embedding, similarity_top_k=retrieve_k, filters=filters, mode=query_mode, query_str=message
        )
    )

    nodes = [
        NodeWithScore(node=node, score=score) for node, score in zip(question_query.nodes, question_query.similarities)
    ]

    if query_mode == VectorStoreQueryMode.SEMANTIC_HYBRID:
        nodes = ScoreScalerPostProcessor(from_min=0, from_max=4).postprocess_nodes(nodes)
    elif query_mode == VectorStoreQueryMode.HYBRID:
        # Milvus hybrid search scores vary based on ranker and data distribution.
        # Use dynamic min-max normalization to produce meaningful relevance percentages.
        nodes = MinMaxScoreNormalizer().postprocess_nodes(nodes)

    return nodes
