from llama_index.core.vector_stores import MetadataFilter, MetadataFilters
from llama_index.core.vector_stores.types import FilterCondition, VectorStoreQuery

from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import NAMESPACE, TYPE
from swiss_ai_hub.core.persistence.rag.vectors.stores.partition_aware_milvus_vector_store import (
    PartitionAwareMilvusVectorStore,
)


def _make_store() -> PartitionAwareMilvusVectorStore:
    """Bypass __init__ — these tests cover pure helpers that don't need a Milvus client."""
    return PartitionAwareMilvusVectorStore.__new__(PartitionAwareMilvusVectorStore)


def test_extract_namespaces_returns_empty_when_query_has_no_filters() -> None:
    store = _make_store()
    query = VectorStoreQuery(query_embedding=[0.1, 0.2], similarity_top_k=5)

    assert store._extract_namespaces_from_query(query) == []


def test_extract_namespaces_from_flat_filters() -> None:
    store = _make_store()
    filters = MetadataFilters(
        filters=[
            MetadataFilter(key=NAMESPACE, value="alpha"),
            MetadataFilter(key=TYPE, value="text"),
        ],
        condition=FilterCondition.AND,
    )
    query = VectorStoreQuery(query_embedding=[0.1], similarity_top_k=5, filters=filters)

    assert store._extract_namespaces_from_query(query) == ["alpha"]


def test_extract_namespaces_from_nested_filters_regression() -> None:
    """
    Regression: MetadataFilters is a Pydantic model — iterating it yields field tuples,
    not filter items. The helper must iterate filters.filters; otherwise no namespace is
    ever found and query() silently loads the full collection.
    """
    store = _make_store()
    filters = MetadataFilters(
        filters=[
            MetadataFilters(
                filters=[
                    MetadataFilter(key=NAMESPACE, value="alpha"),
                    MetadataFilter(key=TYPE, value="text"),
                ],
                condition=FilterCondition.AND,
            ),
            MetadataFilters(
                filters=[
                    MetadataFilter(key=NAMESPACE, value="beta"),
                    MetadataFilter(key=TYPE, value="text"),
                ],
                condition=FilterCondition.AND,
            ),
        ],
        condition=FilterCondition.OR,
    )
    query = VectorStoreQuery(query_embedding=[0.1], similarity_top_k=5, filters=filters)

    assert store._extract_namespaces_from_query(query) == ["alpha", "beta"]


def test_extract_namespaces_ignores_non_namespace_filters() -> None:
    store = _make_store()
    filters = MetadataFilters(
        filters=[
            MetadataFilter(key=TYPE, value="text"),
            MetadataFilter(key="other", value="value"),
        ],
        condition=FilterCondition.AND,
    )
    query = VectorStoreQuery(query_embedding=[0.1], similarity_top_k=5, filters=filters)

    assert store._extract_namespaces_from_query(query) == []


def test_extract_namespaces_ignores_non_string_namespace_values() -> None:
    store = _make_store()
    filters = MetadataFilters(
        filters=[MetadataFilter(key=NAMESPACE, value=["alpha", "beta"])],
        condition=FilterCondition.AND,
    )
    query = VectorStoreQuery(query_embedding=[0.1], similarity_top_k=5, filters=filters)

    assert store._extract_namespaces_from_query(query) == []


def test_extract_namespaces_from_metadata_filters_directly() -> None:
    """get_nodes() calls this helper directly — must accept a MetadataFilters and iterate its inner list."""
    store = _make_store()
    filters = MetadataFilters(
        filters=[MetadataFilter(key=NAMESPACE, value="alpha")],
        condition=FilterCondition.AND,
    )

    assert store._extract_namespaces_from_metadata_filters(filters) == ["alpha"]
