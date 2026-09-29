import json
from unittest.mock import MagicMock

import pytest
from llama_index.core.schema import NodeRelationship, RelatedNodeInfo, TextNode
from llama_index.core.vector_stores import MetadataFilter, MetadataFilters
from llama_index.core.vector_stores.types import FilterCondition, VectorStoreQuery
from llama_index.core.vector_stores.utils import metadata_dict_to_node, node_to_metadata_dict

from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import DOCUMENT_ID, NAMESPACE, TYPE
from swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_partition_manager import (
    DEFAULT_PARTITION_NAME,
    get_partition_name_for_namespace,
)
from swiss_ai_hub.core.persistence.rag.vectors.stores.partition_aware_milvus_vector_store import (
    DOCUMENT_IDS_PER_DELETE_EXPRESSION,
    MILVUS_DYNAMIC_FIELD_MAX_BYTES,
    NODE_IDS_PER_DELETE,
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


class _StubMilvusClient:
    """Answers describe_collection with the schema from milvus_vector_store_factory."""

    def __init__(self) -> None:
        self.describe_calls = 0

    def describe_collection(self, collection_name: str) -> dict[str, list[dict[str, str]]]:
        self.describe_calls += 1
        return {
            "fields": [
                {"name": name} for name in ("id", DOCUMENT_ID, NAMESPACE, "embedding", "sparse_embedding", "text")
            ]
        }


def _make_store_with_stub_client() -> PartitionAwareMilvusVectorStore:
    """__init__ needs a live Milvus; these tests only need collection_name and a describe_collection."""
    store = _make_store()
    object.__setattr__(store, "__dict__", {"collection_name": "defaultknowledge"})
    store._milvusclient = _StubMilvusClient()
    store._declared_fields = None
    return store


def _make_summary_node(child_count: int) -> TextNode:
    """A summary node shaped like the one that broke ingestion: one CHILD entry per descendant."""
    return TextNode(
        text="summary",
        metadata={DOCUMENT_ID: "6b5447776c2e3176da636a57", NAMESPACE: "embre-new"},
        relationships={
            NodeRelationship.SOURCE: RelatedNodeInfo(node_id="source-doc"),
            NodeRelationship.PARENT: RelatedNodeInfo(node_id="root-summary"),
            NodeRelationship.PREVIOUS: RelatedNodeInfo(node_id="previous-summary"),
            NodeRelationship.NEXT: RelatedNodeInfo(node_id="next-summary"),
            NodeRelationship.CHILD: [
                RelatedNodeInfo(node_id=f"{index:08x}-4b1e-4f8a-9c2d-{index:012x}") for index in range(child_count)
            ],
        },
    )


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


def _store_for_document_deletes(
    client: MagicMock, has_manual_partitions: bool = True
) -> PartitionAwareMilvusVectorStore:
    store = _store_with_client(client, has_manual_partitions=has_manual_partitions)
    store.doc_id_field = DOCUMENT_ID
    client.delete.return_value = {"delete_count": 2}
    return store


def test_document_delete_loads_only_the_namespace_partitions_and_default() -> None:
    """Loading the whole collection is ~54 GB on a partitioned store; a removal must never do it."""
    client = MagicMock()
    store = _store_for_document_deletes(client)

    store.delete_documents(["doc1"], ["alpha", "beta", "alpha"])

    expected_partitions = [
        get_partition_name_for_namespace("alpha"),
        get_partition_name_for_namespace("beta"),
        DEFAULT_PARTITION_NAME,
    ]
    client.load_partitions.assert_called_once_with(collection_name="tenant_db", partition_names=expected_partitions)
    client.load_collection.assert_not_called()
    assert [call.kwargs["partition_name"] for call in client.delete.call_args_list] == expected_partitions


def test_document_delete_is_a_filter_on_the_document_id_field() -> None:
    client = MagicMock()
    store = _store_for_document_deletes(client)

    deleted = store.delete_documents(["doc1", "doc2"], ["alpha"])

    client.delete.assert_any_call(
        collection_name="tenant_db",
        filter=f'{DOCUMENT_ID} in ["doc1","doc2"]',
        partition_name=get_partition_name_for_namespace("alpha"),
    )
    client.query.assert_not_called()
    assert deleted == 4


def test_document_delete_batches_the_id_expression() -> None:
    client = MagicMock()
    store = _store_for_document_deletes(client, has_manual_partitions=False)
    ids = [f"doc{index}" for index in range(DOCUMENT_IDS_PER_DELETE_EXPRESSION + 1)]

    store.delete_documents(ids, ["alpha"])

    filters = [call.kwargs["filter"] for call in client.delete.call_args_list]
    assert len(filters) == 2
    assert filters[0].count('"doc') == DOCUMENT_IDS_PER_DELETE_EXPRESSION
    assert filters[1] == f'{DOCUMENT_ID} in ["doc{DOCUMENT_IDS_PER_DELETE_EXPRESSION}"]'


def test_document_delete_on_a_legacy_collection_targets_default_only() -> None:
    client = MagicMock()
    store = _store_for_document_deletes(client, has_manual_partitions=False)

    store.delete_documents(["doc1"], ["alpha"])

    client.load_partitions.assert_called_once_with(
        collection_name="tenant_db", partition_names=[DEFAULT_PARTITION_NAME]
    )
    client.load_collection.assert_not_called()
    assert [call.kwargs["partition_name"] for call in client.delete.call_args_list] == [DEFAULT_PARTITION_NAME]


def test_document_delete_matching_nothing_succeeds() -> None:
    """pymilvus omits a zero delete_count; a retried removal of already deleted nodes must still pass."""
    client = MagicMock()
    store = _store_for_document_deletes(client)
    client.delete.return_value = {}

    assert store.delete_documents(["doc1"], ["alpha"]) == 0


def test_document_delete_without_ids_touches_nothing() -> None:
    client = MagicMock()
    store = _store_for_document_deletes(client)

    assert store.delete_documents([], ["alpha"]) == 0

    client.load_partitions.assert_not_called()
    client.delete.assert_not_called()


def test_node_ids_are_grouped_by_document_while_paging_one_partition() -> None:
    client = MagicMock()
    store = _store_for_document_deletes(client)
    iterator = client.query_iterator.return_value
    iterator.next.side_effect = [
        [{"id": "n1", DOCUMENT_ID: "doc1"}, {"id": "n2", DOCUMENT_ID: "doc2"}],
        [{"id": "n3", DOCUMENT_ID: "doc1"}],
        [],
    ]

    node_ids = store.node_ids_by_document("partition_7")

    assert node_ids == {"doc1": ["n1", "n3"], "doc2": ["n2"]}
    client.load_partitions.assert_called_once_with(collection_name="tenant_db", partition_names=["partition_7"])
    assert client.query_iterator.call_args.kwargs["partition_names"] == ["partition_7"]
    iterator.close.assert_called_once()


def test_nodes_are_deleted_by_primary_key_in_batches() -> None:
    client = MagicMock()
    store = _store_for_document_deletes(client)
    client.delete.side_effect = lambda **kwargs: kwargs["ids"]
    node_ids = [f"n{index}" for index in range(NODE_IDS_PER_DELETE + 5)]

    deleted = store.delete_nodes_in_partition(node_ids, DEFAULT_PARTITION_NAME)

    assert deleted == len(node_ids)
    assert [len(call.kwargs["ids"]) for call in client.delete.call_args_list] == [NODE_IDS_PER_DELETE, 5]
    assert {call.kwargs["partition_name"] for call in client.delete.call_args_list} == {DEFAULT_PARTITION_NAME}


def test_stripping_children_keeps_summary_node_under_the_dynamic_field_limit() -> None:
    """
    Regression for #155: a summary node over a flat document accumulates one CHILD entry per section,
    and the serialized node exceeds Milvus' dynamic field cap long before the tree gets deep.
    """
    store = _make_store()
    node = _make_summary_node(child_count=500)

    assert store._json_size_in_bytes(node_to_metadata_dict(node, remove_text=True)) > MILVUS_DYNAMIC_FIELD_MAX_BYTES

    sanitized = store._without_child_relationship(node)
    entry = node_to_metadata_dict(sanitized, remove_text=True)

    assert store._json_size_in_bytes(entry) <= MILVUS_DYNAMIC_FIELD_MAX_BYTES


def test_stripping_children_preserves_every_other_relationship() -> None:
    store = _make_store()

    sanitized = store._without_child_relationship(_make_summary_node(child_count=10))

    assert set(sanitized.relationships) == {
        NodeRelationship.SOURCE,
        NodeRelationship.PARENT,
        NodeRelationship.PREVIOUS,
        NodeRelationship.NEXT,
    }
    assert sanitized.relationships[NodeRelationship.PARENT].node_id == "root-summary"


def test_stripping_children_does_not_mutate_the_callers_node() -> None:
    """add() receives nodes that stay in use downstream — persistence must not edit them in place."""
    store = _make_store()
    node = _make_summary_node(child_count=10)

    store._without_child_relationship(node)

    assert len(node.relationships[NodeRelationship.CHILD]) == 10


def test_node_without_children_is_returned_unchanged() -> None:
    store = _make_store()
    node = TextNode(text="content", relationships={NodeRelationship.SOURCE: RelatedNodeInfo(node_id="source-doc")})

    assert store._without_child_relationship(node) is node


def test_children_are_not_restored_on_read() -> None:
    """
    Pins the trade-off: the stored node has no child list, so nothing can silently reintroduce the
    overflow by round-tripping it. Consumers walk PARENT upward instead.
    """
    store = _make_store()
    entry = node_to_metadata_dict(store._without_child_relationship(_make_summary_node(child_count=10)))

    restored = metadata_dict_to_node(entry)

    assert restored.child_nodes is None
    assert restored.parent_node.node_id == "root-summary"


def test_guard_names_the_document_and_node_when_the_dynamic_field_overflows() -> None:
    store = _make_store()
    node = _make_summary_node(child_count=500)
    dynamic_field = node_to_metadata_dict(node, remove_text=True)

    with pytest.raises(ValueError) as exception_info:
        store._verify_dynamic_field_fits(dynamic_field, node)

    message = str(exception_info.value)
    assert node.node_id in message
    assert "6b5447776c2e3176da636a57" in message
    assert "_node_content" in message


def test_declared_columns_do_not_count_toward_the_dynamic_field() -> None:
    """
    The split must mirror pymilvus' own (`k not in fields_data`, prepare.py). Counting declared columns
    would reject entries Milvus accepts — text alone is allowed a full 65535 bytes of its own.
    """
    store = _make_store_with_stub_client()
    node = _make_summary_node(child_count=0)
    entry = node_to_metadata_dict(node, remove_text=True)
    entry.update(
        {
            "id": node.node_id,
            "text": "x" * MILVUS_DYNAMIC_FIELD_MAX_BYTES,
            "embedding": [0.123456789] * 4096,
            "sparse_embedding": {1: 0.5},
        }
    )

    store._verify_entry_fits(entry, node)


def test_undeclared_keys_do_count_toward_the_dynamic_field() -> None:
    """The mirror of the above: missing a key that Milvus packs would make the guard decorative."""
    store = _make_store_with_stub_client()
    node = _make_summary_node(child_count=0)
    entry = node_to_metadata_dict(node, remove_text=True)
    entry["table_refinement"] = "x" * MILVUS_DYNAMIC_FIELD_MAX_BYTES

    with pytest.raises(ValueError):
        store._verify_entry_fits(entry, node)


def test_declared_field_names_are_resolved_once_and_cached() -> None:
    store = _make_store_with_stub_client()
    expected = {"id", DOCUMENT_ID, NAMESPACE, "embedding", "sparse_embedding", "text"}

    assert store._declared_field_names() == expected
    assert store._declared_field_names() == expected
    assert store.client.describe_calls == 1


def test_size_matches_how_pymilvus_serializes_the_dynamic_field() -> None:
    """pymilvus packs the dynamic field with orjson, which emits compact separators and raw UTF-8."""
    orjson = pytest.importorskip("orjson")
    store = _make_store()
    dynamic_field = node_to_metadata_dict(_make_summary_node(child_count=20), remove_text=True)

    assert store._json_size_in_bytes(dynamic_field) == len(orjson.dumps(dynamic_field))


def test_guard_measures_bytes_not_characters() -> None:
    """Milvus rejects on UTF-8 byte length; a two-byte-per-character payload fits by count and not by size."""
    store = _make_store()
    payload = "ü" * (MILVUS_DYNAMIC_FIELD_MAX_BYTES // 2)
    dynamic_field = {"_node_content": payload}
    node = _make_summary_node(child_count=0)

    assert len(json.dumps(dynamic_field, ensure_ascii=False)) < MILVUS_DYNAMIC_FIELD_MAX_BYTES

    with pytest.raises(ValueError):
        store._verify_dynamic_field_fits(dynamic_field, node)
