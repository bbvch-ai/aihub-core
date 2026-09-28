from swiss_ai_hub.core.generative_ai.retrievers.bucket_metadata_filters import BucketMetadataFilters
from swiss_ai_hub.core.generative_ai.retrievers.bucket_namespace_pair import BucketNamespacePair
from swiss_ai_hub.core.generative_ai.retrievers.knowledge_retriever_config import KnowledgeRetrieverConfig
from swiss_ai_hub.core.generative_ai.retrievers.metadata_filter_pair import MetadataFilterPair
from swiss_ai_hub.core.generative_ai.retrievers.retrieval_runtime_config import RetrievalRuntimeConfig
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import NAMESPACE


def narrow_retrievers(
    retrievers: list[KnowledgeRetrieverConfig],
    selected_namespaces: list[BucketNamespacePair],
    additional_filters: list[BucketMetadataFilters] | None = None,
) -> list[RetrievalRuntimeConfig]:
    """Narrow configured retrievers by publisher-selected namespaces and runtime metadata filters.

    Primary caller is the `RAGStartEvent` path in RAG agents. The agent's configured namespace scope is
    always the upper bound: a publisher-supplied namespace outside the named set is dropped, a bucket left
    with none of its selected namespaces drops the retriever, and only a retriever configured with
    `all_namespaces` accepts any namespace. Several pairs may name the same bucket, which narrows that
    retriever to all of them rather than to the last one seen.
    `additional_filters` keys must be listed in `allowed_metadata_filter_fields`; the reserved
    `namespace` key is rejected.
    """
    selected_namespaces_by_bucket = _index_namespaces_by_bucket(selected_namespaces)
    filters_by_bucket = _index_filters_by_bucket(additional_filters)

    _reject_unknown_buckets(filters_by_bucket, retrievers)

    runtime_configs: list[RetrievalRuntimeConfig] = []
    for retriever in retrievers:
        bucket = retriever.vector_store.collection_name

        # Publisher made a selection but this bucket isn't in it — drop.
        if selected_namespaces_by_bucket and bucket not in selected_namespaces_by_bucket:
            continue

        narrowed_config = retriever
        if bucket in selected_namespaces_by_bucket:
            configured = retriever.vector_store
            within_scope = [
                namespace
                for namespace in selected_namespaces_by_bucket[bucket]
                if configured.all_namespaces or namespace in configured.index_namespaces
            ]
            # Every selected namespace for this bucket is outside the agent's configured set — drop.
            if not within_scope:
                continue
            narrowed_vector_store = configured.model_copy(
                update={"index_namespaces": within_scope, "all_namespaces": False}
            )
            narrowed_config = retriever.model_copy(update={"vector_store": narrowed_vector_store})

        runtime_filters = filters_by_bucket.get(bucket, [])
        if runtime_filters:
            _validate_filter_keys(runtime_filters, retriever.vector_store.allowed_metadata_filter_fields, bucket)

        runtime_configs.append(
            RetrievalRuntimeConfig(config=narrowed_config, additional_metadata_filters=runtime_filters)
        )

    return runtime_configs


def _index_namespaces_by_bucket(selected_namespaces: list[BucketNamespacePair]) -> dict[str, list[str]]:
    """Group the selection by bucket, keeping order and dropping repeats — a namespace listed twice would otherwise
    reach Milvus twice in one filter."""
    namespaces_by_bucket: dict[str, list[str]] = {}
    for pair in selected_namespaces:
        namespaces = namespaces_by_bucket.setdefault(pair.bucket_name, [])
        if pair.namespace_name not in namespaces:
            namespaces.append(pair.namespace_name)
    return namespaces_by_bucket


def _index_filters_by_bucket(
    additional_filters: list[BucketMetadataFilters] | None,
) -> dict[str, list[MetadataFilterPair]]:
    filters_by_bucket: dict[str, list[MetadataFilterPair]] = {}
    for entry in additional_filters or []:
        if entry.bucket_name in filters_by_bucket:
            raise ValueError(
                f"Duplicate additional_filters entry for bucket '{entry.bucket_name}'. "
                f"Merge all filters for a bucket into a single BucketMetadataFilters."
            )
        filters_by_bucket[entry.bucket_name] = entry.filters
    return filters_by_bucket


def _validate_filter_keys(filters: list[MetadataFilterPair], allowed_keys: list[str], bucket: str) -> None:
    allowed = set(allowed_keys)
    for f in filters:
        if f.key == NAMESPACE:
            raise ValueError(
                f"Filter key '{NAMESPACE}' is reserved and cannot be used in additional_filters "
                f"(bucket '{bucket}'). Use `selected_namespaces` instead."
            )
        if f.key not in allowed:
            raise ValueError(
                f"Filter key '{f.key}' is not allowed on bucket '{bucket}'. Allowed keys: {sorted(allowed)}"
            )


def _reject_unknown_buckets(
    filters_by_bucket: dict[str, list[MetadataFilterPair]],
    retrievers: list[KnowledgeRetrieverConfig],
) -> None:
    configured_buckets = {r.vector_store.collection_name for r in retrievers}
    unknown_buckets = set(filters_by_bucket) - configured_buckets
    if unknown_buckets:
        raise ValueError(
            f"additional_filters references unknown bucket(s): {sorted(unknown_buckets)}. "
            f"Configured buckets: {sorted(configured_buckets)}"
        )
