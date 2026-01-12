from aihub_lib.generative_ai.retrievers.BucketNamespacePair import BucketNamespacePair
from aihub_lib.generative_ai.retrievers.KnowledgeRetrieverConfig import KnowledgeRetrieverConfig
from aihub_lib.generative_ai.retrievers.RetrieverConfig import RetrieverConfig


def filter_retrievers_by_namespace(
    retrievers: list[RetrieverConfig],
    selected_namespaces: list[BucketNamespacePair],
) -> list[RetrieverConfig]:
    """Filter KnowledgeRetrieverConfigs to use only selected namespaces.

    Non-knowledge retrievers (e.g., InsightRetrieverConfig) pass through unchanged.
    """
    if not selected_namespaces:
        return retrievers

    namespace_map = {pair.bucket_name: pair.namespace_name for pair in selected_namespaces}

    filtered: list[RetrieverConfig] = []
    for retriever in retrievers:
        if isinstance(retriever, KnowledgeRetrieverConfig):
            bucket_name = retriever.vector_store.collection_name
            if bucket_name in namespace_map:
                selected_namespace = namespace_map[bucket_name]
                if not retriever.index_namespaces or selected_namespace in retriever.index_namespaces:
                    filtered_retriever = retriever.model_copy(update={"index_namespaces": [selected_namespace]})
                    filtered.append(filtered_retriever)
        else:
            filtered.append(retriever)
    return filtered
