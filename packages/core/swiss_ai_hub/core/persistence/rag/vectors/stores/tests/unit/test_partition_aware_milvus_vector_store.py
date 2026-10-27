import json
from typing import Any
from unittest.mock import MagicMock, call

import pytest
from llama_index.core.schema import NodeRelationship, RelatedNodeInfo, TextNode
from llama_index.core.vector_stores import MetadataFilter, MetadataFilters
from llama_index.core.vector_stores.types import FilterCondition, VectorStoreQuery, VectorStoreQueryResult
from llama_index.core.vector_stores.utils import metadata_dict_to_node, node_to_metadata_dict
from llama_index.vector_stores.milvus import MilvusVectorStore

from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import DOCUMENT_ID, NAMESPACE, TYPE
from swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_partition_manager import (
    DEFAULT_PARTITION_NAME,
    MANUAL_PARTITIONS_MARKER,
    MAX_PARTITIONS,
    create_manual_partitions,
    get_partition_name,
    get_partition_name_for_namespace,
)
from swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_partition_state import MilvusPartitionState
from swiss_ai_hub.core.persistence.rag.vectors.stores.partition_aware_milvus_vector_store import (
    DOCUMENT_IDS_PER_DELETE_EXPRESSION,
    MILVUS_DYNAMIC_FIELD_MAX_BYTES,
    NODE_IDS_PER_DELETE,
    PartitionAwareMilvusVectorStore,
)


def _make_store() -> PartitionAwareMilvusVectorStore:
    """Bypass __init__ — these tests cover pure helpers that don't need a Milvus client."""
    return PartitionAwareMilvusVectorStore.__new__(PartitionAwareMilvusVectorStore)


def _store_with_client(
    client: Any, partition_state: MilvusPartitionState | None = MilvusPartitionState.COMPLETE
) -> PartitionAwareMilvusVectorStore:
    """Bypass pydantic init to inject a client; ``partition_state=None`` makes the store read it from the client."""
    store = PartitionAwareMilvusVectorStore.__new__(PartitionAwareMilvusVectorStore)
    object.__setattr__(store, "__dict__", {})
    object.__setattr__(store, "__pydantic_private__", {})
    object.__setattr__(store, "__pydantic_fields_set__", set())
    object.__setattr__(store, "__pydantic_extra__", {})
    store._milvusclient = client
    store._settled_partition_state = partition_state
    store._collection_description = None
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
    store._collection_description = None
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


def test_delete_by_namespace_is_a_filtered_delete_scoped_to_the_namespace_partition_and_default() -> None:
    """Shared-partition safety: namespace cleanup MUST filter by ``namespace ==`` and target only that
    namespace's hashed partition and ``_default`` — never drop a partition, which would wipe colliding
    namespaces. ``_default`` holds nodes stranded by #1923 that all-namespaces retrieval still finds."""
    client = MagicMock()
    store = _store_with_client(client)

    store.delete_by_namespace("alpha")

    client.load_partitions.assert_called_once_with(
        collection_name="tenant_db",
        partition_names=[get_partition_name_for_namespace("alpha"), DEFAULT_PARTITION_NAME],
    )
    assert client.delete.call_args_list == [
        call(
            collection_name="tenant_db",
            filter=f'{NAMESPACE} == "alpha"',
            partition_name=get_partition_name_for_namespace("alpha"),
        ),
        call(collection_name="tenant_db", filter=f'{NAMESPACE} == "alpha"', partition_name=DEFAULT_PARTITION_NAME),
    ]
    client.load_collection.assert_not_called()
    client.drop_partition.assert_not_called()


def test_delete_by_namespace_without_manual_partitions_deletes_collection_wide() -> None:
    client = MagicMock()
    store = _store_with_client(client, partition_state=MilvusPartitionState.LEGACY)

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
    client: MagicMock, partition_state: MilvusPartitionState = MilvusPartitionState.COMPLETE
) -> PartitionAwareMilvusVectorStore:
    store = _store_with_client(client, partition_state=partition_state)
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
    store = _store_for_document_deletes(client, partition_state=MilvusPartitionState.LEGACY)
    ids = [f"doc{index}" for index in range(DOCUMENT_IDS_PER_DELETE_EXPRESSION + 1)]

    store.delete_documents(ids, ["alpha"])

    filters = [call.kwargs["filter"] for call in client.delete.call_args_list]
    assert len(filters) == 2
    assert filters[0].count('"doc') == DOCUMENT_IDS_PER_DELETE_EXPRESSION
    assert filters[1] == f'{DOCUMENT_ID} in ["doc{DOCUMENT_IDS_PER_DELETE_EXPRESSION}"]'


def test_document_delete_on_a_legacy_collection_targets_default_only() -> None:
    client = MagicMock()
    store = _store_for_document_deletes(client, partition_state=MilvusPartitionState.LEGACY)

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


_ALL_MANUAL_PARTITIONS = [get_partition_name(partition_id) for partition_id in range(MAX_PARTITIONS)]


class _PartitionStubClient:
    """A collection with the given manual partitions; rejects unknown partition names the way Milvus does."""

    def __init__(self, manual_partitions: list[str], marker: bool = True) -> None:
        self.partitions = [DEFAULT_PARTITION_NAME, *manual_partitions]
        self.description = MANUAL_PARTITIONS_MARKER if marker else ""
        self.list_calls = 0
        self.written_partitions: list[str] = []

    def list_partitions(self, collection_name: str) -> list[str]:
        self.list_calls += 1
        return list(self.partitions)

    def describe_collection(self, collection_name: str) -> dict[str, Any]:
        fields = ("id", DOCUMENT_ID, NAMESPACE, "embedding", "sparse_embedding", "text")
        return {"description": self.description, "fields": [{"name": name} for name in fields]}

    def create_partition(self, collection_name: str, partition_name: str) -> None:
        if partition_name not in self.partitions:
            self.partitions.append(partition_name)

    def load_partitions(self, collection_name: str, partition_names: list[str]) -> None:
        missing = set(partition_names) - set(self.partitions)
        if missing:
            raise ValueError(f"partition not found: {sorted(missing)}")

    def load_collection(self, collection_name: str) -> None:
        pass

    def upsert(self, collection_name: str, data: list[dict[str, Any]], partition_name: str | None = None) -> None:
        self.written_partitions.append(partition_name or DEFAULT_PARTITION_NAME)


def _writable_store(client: _PartitionStubClient) -> PartitionAwareMilvusVectorStore:
    store = _store_with_client(client, partition_state=None)
    store.text_key = "text"
    store.enable_dense = True
    store.embedding_field = "embedding"
    store.enable_sparse = False
    store.upsert_mode = True
    store.batch_size = 100
    return store


def _node_in(namespace: str) -> TextNode:
    return TextNode(text="content", metadata={DOCUMENT_ID: "doc1", NAMESPACE: namespace}, embedding=[0.1, 0.2])


def _without(partition_name: str) -> list[str]:
    return [name for name in _ALL_MANUAL_PARTITIONS if name != partition_name]


@pytest.mark.parametrize("marker", [True, False], ids=["created-with-marker", "created-before-the-marker"])
def test_a_half_built_collection_is_completed_before_a_write_and_nothing_lands_in_default(marker: bool) -> None:
    """#1923: the e2egdrive collection had 868 of its partitions; every write of every process went to _default."""
    client = _PartitionStubClient(_ALL_MANUAL_PARTITIONS[:868], marker=marker)
    store = _writable_store(client)

    store.add([_node_in("alpha")])

    assert len(client.partitions) == MAX_PARTITIONS + 1
    assert client.written_partitions == [get_partition_name_for_namespace("alpha")]
    assert store.partition_state() is MilvusPartitionState.COMPLETE


def test_a_marked_collection_without_partitions_is_half_built_not_legacy() -> None:
    """Its creator has not yet created a partition, or died before the first one."""
    store = _store_with_client(_PartitionStubClient([], marker=True), partition_state=None)

    assert store.partition_state() is MilvusPartitionState.PARTIAL


def test_a_collection_without_marker_or_partitions_is_legacy_and_keeps_writing_to_default() -> None:
    client = _PartitionStubClient([], marker=False)
    store = _writable_store(client)

    store.add([_node_in("alpha")])

    assert store.partition_state() is MilvusPartitionState.LEGACY
    assert client.partitions == [DEFAULT_PARTITION_NAME]
    assert client.written_partitions == [DEFAULT_PARTITION_NAME]


def test_a_half_built_state_is_read_again_while_a_settled_one_is_cached() -> None:
    """Pipeline stores live for the whole process; caching PARTIAL is what stranded every later write."""
    client = _PartitionStubClient(_ALL_MANUAL_PARTITIONS[:500])
    store = _store_with_client(client, partition_state=None)

    assert store.partition_state() is MilvusPartitionState.PARTIAL
    client.partitions = [DEFAULT_PARTITION_NAME, *_ALL_MANUAL_PARTITIONS]
    assert store.partition_state() is MilvusPartitionState.COMPLETE
    assert store.partition_state() is MilvusPartitionState.COMPLETE
    assert client.list_calls == 2


def test_ensure_partitions_leaves_a_legacy_collection_unpartitioned() -> None:
    client = _PartitionStubClient([], marker=False)
    store = _store_with_client(client, partition_state=None)

    assert store.ensure_partitions() is MilvusPartitionState.LEGACY
    assert client.partitions == [DEFAULT_PARTITION_NAME]


def test_reads_of_a_half_built_collection_skip_hashed_partitions_that_do_not_exist_yet() -> None:
    """Milvus rejects an unknown partition name, and nothing can be stored in a partition that does not exist."""
    missing = get_partition_name_for_namespace("beta")
    store = _store_with_client(_PartitionStubClient(_without(missing)), partition_state=None)

    assert store.document_partition_names(["alpha", "beta"]) == [
        get_partition_name_for_namespace("alpha"),
        DEFAULT_PARTITION_NAME,
    ]


def test_get_nodes_by_namespace_reads_the_hashed_partition_and_default() -> None:
    """The API node listing goes through here; nodes stranded in _default must stay visible until repaired."""
    client = MagicMock()
    store = _store_with_client(client)
    expected = [get_partition_name_for_namespace("alpha"), DEFAULT_PARTITION_NAME]

    store.get_nodes(
        filters=MetadataFilters(filters=[MetadataFilter(key=DOCUMENT_ID, value="doc1")]), namespaces=["alpha"]
    )

    client.load_partitions.assert_called_once_with(collection_name="tenant_db", partition_names=expected)
    assert client.query.call_args.kwargs["partition_names"] == expected


def test_get_nodes_by_namespace_on_a_legacy_collection_reads_default() -> None:
    client = MagicMock()
    store = _store_with_client(client, partition_state=MilvusPartitionState.LEGACY)

    store.get_nodes(
        filters=MetadataFilters(filters=[MetadataFilter(key=DOCUMENT_ID, value="doc1")]), namespaces=["alpha"]
    )

    assert client.query.call_args.kwargs["partition_names"] == [DEFAULT_PARTITION_NAME]


def test_query_by_namespace_searches_the_hashed_partition_and_default(monkeypatch: pytest.MonkeyPatch) -> None:
    client = MagicMock()
    store = _store_with_client(client)
    searched: dict[str, Any] = {}
    monkeypatch.setattr(
        MilvusVectorStore, "query", lambda self, query, **kwargs: searched.update(kwargs) or VectorStoreQueryResult()
    )
    filters = MetadataFilters(filters=[MetadataFilter(key=NAMESPACE, value="alpha")])

    store.query(VectorStoreQuery(query_embedding=[0.1], similarity_top_k=5, filters=filters))

    assert searched["milvus_partition_names"] == [get_partition_name_for_namespace("alpha"), DEFAULT_PARTITION_NAME]


def test_create_manual_partitions_creates_only_the_missing_ones() -> None:
    client = MagicMock()
    client.list_partitions.return_value = [DEFAULT_PARTITION_NAME, "partition_0", "partition_5"]

    create_manual_partitions(client=client, collection_name="tenant_db")

    created = [call.kwargs["partition_name"] for call in client.create_partition.call_args_list]
    assert len(created) == MAX_PARTITIONS - 2
    assert "partition_0" not in created
    assert "partition_5" not in created
    client.has_partition.assert_not_called()


def _iterator_over(*pages: list[dict[str, Any]]) -> MagicMock:
    iterator = MagicMock()
    iterator.next.side_effect = [*pages, []]
    return iterator


def test_stranded_nodes_are_read_from_default_without_text_or_vector() -> None:
    client = MagicMock()
    client.query_iterator.return_value = _iterator_over(
        [{"id": "n1", DOCUMENT_ID: "doc1", NAMESPACE: "alpha", TYPE: "summary"}],
        [{"id": "n2", DOCUMENT_ID: "doc1", NAMESPACE: "alpha"}],
    )
    store = _store_for_document_deletes(client)

    stranded = store.stranded_nodes()

    assert [(node.node_id, node.node_type) for node in stranded] == [("n1", "summary"), ("n2", None)]
    assert client.query_iterator.call_args.kwargs["partition_names"] == [DEFAULT_PARTITION_NAME]
    assert client.query_iterator.call_args.kwargs["output_fields"] == ["id", DOCUMENT_ID, NAMESPACE, TYPE]


def test_a_legacy_collection_has_no_stranded_nodes() -> None:
    """All of a legacy collection's nodes belong in _default; none of them may be moved."""
    client = MagicMock()
    store = _store_for_document_deletes(client, partition_state=MilvusPartitionState.LEGACY)

    assert store.stranded_nodes() == []
    client.query_iterator.assert_not_called()


def test_node_keys_of_a_document_are_read_from_its_namespace_partition() -> None:
    client = MagicMock()
    client.query_iterator.return_value = _iterator_over([])
    store = _store_for_document_deletes(client)

    store.node_keys_of_document("doc1", "alpha")

    assert client.query_iterator.call_args.kwargs["partition_names"] == [get_partition_name_for_namespace("alpha")]
    assert client.query_iterator.call_args.kwargs["filter"] == f'{DOCUMENT_ID} == "doc1"'


def test_restoring_copies_stored_rows_into_the_namespace_partition_and_flushes() -> None:
    """Rows are copied as stored, so nothing is parsed or embedded again; the flush makes the copy durable before
    the caller deletes the originals."""
    client = MagicMock()
    rows = [{"id": "n1", "text": "a", "embedding": [0.1]}, {"id": "n2", "text": "b", "embedding": [0.2]}]
    client.query_iterator.return_value = _iterator_over(rows)
    store = _store_for_document_deletes(client)
    store.batch_size = 1

    copied = store.restore_stranded_nodes({"alpha": ["n1", "n2"]})

    assert copied == 2
    scan = client.query_iterator.call_args.kwargs
    assert (scan["partition_names"], scan["output_fields"], scan["filter"]) == (
        [DEFAULT_PARTITION_NAME],
        ["*"],
        'id in ["n1","n2"]',
    )
    target = get_partition_name_for_namespace("alpha")
    assert client.upsert.call_args_list == [
        call(collection_name="tenant_db", data=[rows[0]], partition_name=target),
        call(collection_name="tenant_db", data=[rows[1]], partition_name=target),
    ]
    assert client.mock_calls.index(call.flush("tenant_db")) > client.mock_calls.index(
        call.upsert(collection_name="tenant_db", data=[rows[1]], partition_name=target)
    )


def test_restoring_several_namespaces_flushes_once_after_the_last_copy() -> None:
    """Milvus allows a collection one flush every 10 s; a flush per namespace or document throttles the repair."""
    client = MagicMock()
    alpha_row = {"id": "n1", "text": "a", "embedding": [0.1]}
    beta_row = {"id": "n2", "text": "b", "embedding": [0.2]}
    client.query_iterator.side_effect = [_iterator_over([alpha_row]), _iterator_over([beta_row])]
    store = _store_for_document_deletes(client)
    store.batch_size = 10

    copied = store.restore_stranded_nodes({"alpha": ["n1"], "beta": ["n2"], "gamma": []})

    assert copied == 2
    assert client.upsert.call_args_list == [
        call(collection_name="tenant_db", data=[alpha_row], partition_name=get_partition_name_for_namespace("alpha")),
        call(collection_name="tenant_db", data=[beta_row], partition_name=get_partition_name_for_namespace("beta")),
    ]
    client.flush.assert_called_once_with("tenant_db")
    assert client.mock_calls[-1] == call.flush("tenant_db")
    assert client.query_iterator.call_count == 2


def test_restoring_nothing_neither_loads_nor_flushes() -> None:
    client = MagicMock()
    store = _store_for_document_deletes(client)

    assert store.restore_stranded_nodes({"alpha": []}) == 0
    client.load_partitions.assert_not_called()
    client.query_iterator.assert_not_called()
    client.flush.assert_not_called()


def test_stranded_nodes_are_deleted_from_default_only() -> None:
    client = MagicMock()
    client.delete.side_effect = lambda **kwargs: kwargs["ids"]
    store = _store_for_document_deletes(client)

    assert store.delete_stranded_nodes(["n1", "n2"]) == 2
    client.delete.assert_called_once_with(
        collection_name="tenant_db", ids=["n1", "n2"], partition_name=DEFAULT_PARTITION_NAME
    )


def test_passages_grouped_by_document_search_only_the_namespaces_partitions_grouped_in_milvus() -> None:
    client = MagicMock()
    client.search.return_value = [
        [
            {"distance": 0.8, "entity": {DOCUMENT_ID: "doc1", "text": "Liability is limited"}},
            {"distance": 0.5, "entity": {DOCUMENT_ID: "doc2", "text": "Termination"}},
        ]
    ]
    store = _store_with_client(client)
    store.embedding_field, store.doc_id_field, store.text_key, store.similarity_metric = (
        "embedding",
        DOCUMENT_ID,
        "text",
        "IP",
    )

    hits = store.passages_grouped_by_document([0.1], ["alpha"], 'document_id in ["doc1"]', 10, 5, timeout=3.0)

    partitions = [get_partition_name_for_namespace("alpha"), DEFAULT_PARTITION_NAME]
    client.load_partitions.assert_called_once_with(collection_name="tenant_db", partition_names=partitions)
    search = client.search.call_args.kwargs
    assert (search["group_by_field"], search["group_size"], search["limit"]) == (DOCUMENT_ID, 5, 10)
    assert search["partition_names"] == partitions
    assert search["timeout"] == 3.0
    assert search["filter"] == 'document_id in ["doc1"]'
    assert [(hit.document_id, hit.score) for hit in hits] == [("doc1", 0.8), ("doc2", 0.5)]


def test_documents_with_passages_asks_for_one_hit_per_document_and_no_text() -> None:
    client = MagicMock()
    client.search.return_value = [[{"distance": 0.8, "entity": {DOCUMENT_ID: "doc1"}}]]
    store = _store_with_client(client)
    store.embedding_field, store.doc_id_field, store.text_key, store.similarity_metric = (
        "embedding",
        DOCUMENT_ID,
        "text",
        "IP",
    )

    found = store.documents_with_passages([0.1], ["alpha"], 'document_id in ["doc1", "doc2"]', 2)

    search = client.search.call_args.kwargs
    assert (search["group_size"], search["limit"], search["output_fields"]) == (1, 2, [DOCUMENT_ID])
    assert found == {"doc1"}
