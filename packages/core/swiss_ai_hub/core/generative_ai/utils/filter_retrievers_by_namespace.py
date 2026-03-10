from swiss_ai_hub.core.generative_ai.retrievers.BucketNamespacePair import BucketNamespacePair
from swiss_ai_hub.core.generative_ai.retrievers.KnowledgeRetrieverConfig import KnowledgeRetrieverConfig


def filter_retrievers_by_namespace(
    retrievers: list[KnowledgeRetrieverConfig],
    selected_namespaces: list[BucketNamespacePair],
) -> list[KnowledgeRetrieverConfig]:
    """Filter KnowledgeRetrieverConfigs to use only selected namespaces."""
    if not selected_namespaces:
        return retrievers

    namespace_map = {pair.bucket_name: pair.namespace_name for pair in selected_namespaces}

    filtered: list[KnowledgeRetrieverConfig] = []
    for retriever in retrievers:
        bucket_name = retriever.vector_store.collection_name
        if bucket_name in namespace_map:
            selected_namespace = namespace_map[bucket_name]
            current_namespaces = retriever.vector_store.index_namespaces
            if not current_namespaces or selected_namespace in current_namespaces:
                updated_store = retriever.vector_store.model_copy(update={"index_namespaces": [selected_namespace]})
                filtered_retriever = retriever.model_copy(update={"vector_store": updated_store})
                filtered.append(filtered_retriever)
    return filtered
