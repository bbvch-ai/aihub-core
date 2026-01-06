"""
Retriever building utilities for RAG agents.

Provides functionality to dynamically build retrievers from knowledge sources,
used by both RAGAgent and ExpertRAGAgent when handling RAGWithSourcesStartEvent.
"""

from aihub_lib.generative_ai.retrievers.KnowledgeRetrieverConfig import KnowledgeRetrieverConfig
from aihub_lib.generative_ai.retrievers.RetrieverConfig import RetrieverConfig
from aihub_lib.nats.events import KnowledgeSource


def build_retrievers_from_sources(
    sources: list[KnowledgeSource],
    existing_retrievers: list[RetrieverConfig],
) -> list[KnowledgeRetrieverConfig]:
    """
    Build KnowledgeRetrieverConfig list from KnowledgeSource list.

    Uses existing retriever configurations and only overrides the index_namespaces field.
    Each bucket in sources must have a corresponding KnowledgeRetrieverConfig in existing_retrievers.

    Args:
        sources: Knowledge sources specifying bucket/namespace pairs to query.
        existing_retrievers: Base retriever configurations to clone settings from.

    Returns:
        List of KnowledgeRetrieverConfig with namespaces set from sources.

    Raises:
        ValueError: If no KnowledgeRetrieverConfig found in existing_retrievers,
            or if a bucket in sources has no corresponding retriever configured.
    """
    # Build lookup of existing retrievers by bucket name
    bucket_retrievers: dict[str, KnowledgeRetrieverConfig] = {}
    for retriever in existing_retrievers:
        if isinstance(retriever, KnowledgeRetrieverConfig):
            bucket_name = retriever.vector_store.collection_name
            bucket_retrievers[bucket_name] = retriever

    if not bucket_retrievers:
        raise ValueError(
            "Cannot build dynamic retrievers: no KnowledgeRetrieverConfig found in existing_retrievers. "
            "At least one KnowledgeRetrieverConfig is required."
        )

    # Group sources by bucket
    bucket_namespaces: dict[str, list[str]] = {}
    for source in sources:
        if source.bucket_name not in bucket_namespaces:
            bucket_namespaces[source.bucket_name] = []
        bucket_namespaces[source.bucket_name].append(source.namespace_name)

    # Build retrievers by copying existing config and overriding namespaces
    retrievers: list[KnowledgeRetrieverConfig] = []

    for bucket_name, namespaces in bucket_namespaces.items():
        if bucket_name not in bucket_retrievers:
            raise ValueError(
                f"No retriever configured for bucket '{bucket_name}'. "
                "Each bucket used in RAGWithSourcesStartEvent must have a corresponding retriever in agent config."
            )

        base_retriever = bucket_retrievers[bucket_name]
        retrievers.append(
            KnowledgeRetrieverConfig(
                embed_model=base_retriever.embed_model,
                index_namespaces=namespaces,
                retrieve_k=base_retriever.retrieve_k,
                query_mode=base_retriever.query_mode,
                node_types=base_retriever.node_types,
                vector_store=base_retriever.vector_store,
                retrieve_prev_next=base_retriever.retrieve_prev_next,
                retrieve_summaries=base_retriever.retrieve_summaries,
            )
        )

    return retrievers
