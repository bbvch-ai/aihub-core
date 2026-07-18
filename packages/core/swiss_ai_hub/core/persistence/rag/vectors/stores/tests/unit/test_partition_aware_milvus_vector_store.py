from unittest.mock import MagicMock

from llama_index.core.vector_stores import MetadataFilter, MetadataFilters
from llama_index.core.vector_stores.types import FilterCondition, VectorStoreQuery

from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import NAMESPACE, TYPE
from swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_partition_manager import get_partition_name_for_namespace
from swiss_ai_hub.core.persistence.rag.vectors.stores.partition_aware_milvus_vector_store import (
    PartitionAwareMilvusVectorStore,
)


def _make_store() -> PartitionAwareMilvusVectorStore:
    """Bypass __init__ — these tests cover pure helpers that don't need a Milvus client."""
    return PartitionAwareMilvusVectorStore.__new__(PartitionAwareMilvusVectorStore)


def _store_with_client(client: MagicMock, has_manual_partitions: bool = True) -> PartitionAwareMilvusVectorStore:
    """Bypass pydantic init to inject a mock client for the teardown delete/drop paths."""
    store = PartitionAwareMilvusVectorStore.__new__(PartitionAwareMilvusVectorStore)
    object.__setattr__(store, "__dict__", {})
    object.__setattr__(store, "__pydantic_private__", {})
    object.__setattr__(store, "__pydantic_fields_set__", set())
    object.__setattr__(store, "__pydantic_extra__", {})
    store._milvusclient = client
    store._has_manual_partitions = has_manual_partitions
    store.collection_name = "tenant_db"
    return store


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


def test_delete_by_namespace_is_a_filtered_delete_scoped_to_the_namespace_partition() -> None:
    """Shared-partition safety: namespace cleanup MUST filter by ``namespace ==`` and target only that
    namespace's hashed partition — never drop the partition, which would wipe colliding namespaces."""
    client = MagicMock()
    store = _store_with_client(client, has_manual_partitions=True)

    store.delete_by_namespace("alpha")

    client.delete.assert_called_once_with(
        collection_name="tenant_db",
        filter=f'{NAMESPACE} == "alpha"',
        partition_name=get_partition_name_for_namespace("alpha"),
    )
    client.drop_partition.assert_not_called()


def test_delete_by_namespace_without_manual_partitions_deletes_collection_wide() -> None:
    client = MagicMock()
    store = _store_with_client(client, has_manual_partitions=False)

    store.delete_by_namespace("alpha")

    client.delete.assert_called_once_with(
        collection_name="tenant_db",
        filter=f'{NAMESPACE} == "alpha"',
        partition_name=None,
    )


def test_drop_collection_drops_when_present() -> None:
    client = MagicMock()
    client.has_collection.return_value = True
    store = _store_with_client(client)

    store.drop_collection()

    client.drop_collection.assert_called_once_with(collection_name="tenant_db")


def test_drop_collection_is_idempotent_when_absent() -> None:
    client = MagicMock()
    client.has_collection.return_value = False
    store = _store_with_client(client)

    store.drop_collection()

    client.drop_collection.assert_not_called()
