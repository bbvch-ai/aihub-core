from aihub_lib.generative_ai.retrievers.BucketNamespacePair import BucketNamespacePair
from aihub_lib.generative_ai.retrievers.InsightRetrieverConfig import InsightRetrieverConfig
from aihub_lib.generative_ai.retrievers.KnowledgeRetrieverConfig import KnowledgeRetrieverConfig
from aihub_lib.generative_ai.retrievers.RetrieverConfig import RetrieverConfig


def filter_retrievers_by_namespace(
    retrievers: list[RetrieverConfig],
    selected_namespaces: list[BucketNamespacePair],
) -> list[RetrieverConfig]:
    """Filter retriever configs to use only selected namespaces.

    For KnowledgeRetrieverConfig: Filters by bucket name and updates index_namespaces.
    For InsightRetrieverConfig: Sets index_namespaces to compound format "bucket/namespace".
    """
    if not selected_namespaces:
        return retrievers

    namespace_map = {pair.bucket_name: pair.namespace_name for pair in selected_namespaces}
    compound_namespaces = [f"{pair.bucket_name}/{pair.namespace_name}" for pair in selected_namespaces]

    filtered: list[RetrieverConfig] = []
    for retriever in retrievers:
        if isinstance(retriever, KnowledgeRetrieverConfig):
            bucket_name = retriever.vector_store.collection_name
            if bucket_name in namespace_map:
                selected_namespace = namespace_map[bucket_name]
                if not retriever.index_namespaces or selected_namespace in retriever.index_namespaces:
                    filtered.append(retriever.model_copy(update={"index_namespaces": [selected_namespace]}))
        elif isinstance(retriever, InsightRetrieverConfig):
            # Filter InsightRetriever by compound namespaces
            filtered.append(retriever.model_copy(update={"index_namespaces": compound_namespaces}))
        else:
            filtered.append(retriever)
    return filtered
