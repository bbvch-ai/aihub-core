from unittest.mock import patch

from swiss_ai_hub.core.persistence import NODE_TYPE_CONTENT, NODE_TYPE_SUMMARY, MilvusPartitionState, StoredNodeKey

from swiss_ai_hub.pipeline.services.default_partition_repair_service import DefaultPartitionRepairService
from swiss_ai_hub.pipeline.types.default_partition_repair_report import DefaultPartitionRepairReport

_MODULE = "swiss_ai_hub.pipeline.services.default_partition_repair_service"

BUCKET = "handbook"
DB = "handbook_db"
NAMESPACE = "hr"
WIDTH = 3072


def _key(
    node_id: str, node_type: str = NODE_TYPE_CONTENT, document_id: str = "doc1", namespace: str = NAMESPACE
) -> StoredNodeKey:
    return StoredNodeKey(node_id=node_id, document_id=document_id, namespace=namespace, node_type=node_type)


class _FakeVectorStore:
    """A collection's ``_default`` and namespace partition; copies and deletes move keys between them."""

    def __init__(
        self,
        stranded: list[StoredNodeKey],
        present: list[StoredNodeKey] | None = None,
        state: MilvusPartitionState = MilvusPartitionState.COMPLETE,
    ) -> None:
        self.stranded = stranded
        self.present = present or []
        self.state = state
        self.calls: list[tuple] = []

    def ensure_partitions(self) -> MilvusPartitionState:
        self.calls.append(("ensure_partitions",))
        return self.state

    def stranded_nodes(self) -> list[StoredNodeKey]:
        return [] if self.state is MilvusPartitionState.LEGACY else list(self.stranded)

    def node_keys_of_document(self, document_id: str, namespace: str) -> list[StoredNodeKey]:
        return [node for node in self.present if node.document_id == document_id and node.namespace == namespace]

    def restore_stranded_nodes(self, node_ids_by_namespace: dict[str, list[str]]) -> int:
        self.calls.append(("restore", {namespace: sorted(ids) for namespace, ids in node_ids_by_namespace.items()}))
        node_ids = {node_id for ids in node_ids_by_namespace.values() for node_id in ids}
        self.present += [node for node in self.stranded if node.node_id in node_ids]
        return len(node_ids)

    def delete_stranded_nodes(self, node_ids: list[str]) -> int:
        self.calls.append(("delete", sorted(node_ids)))
        self.stranded = [node for node in self.stranded if node.node_id not in node_ids]
        return len(node_ids)


def _repair(vector_store: _FakeVectorStore) -> DefaultPartitionRepairReport:
    with (
        patch(f"{_MODULE}.get_db_name_from_bucket_name", return_value=DB),
        patch(f"{_MODULE}.embedding_dimension_for_bucket", return_value=WIDTH),
        patch(f"{_MODULE}.build_vector_store", return_value=vector_store),
    ):
        return DefaultPartitionRepairService.repair(BUCKET)


def test_the_collection_is_provisioned_with_the_width_of_the_database_embedding_model() -> None:
    with (
        patch(f"{_MODULE}.get_db_name_from_bucket_name", return_value=DB),
        patch(f"{_MODULE}.embedding_dimension_for_bucket", return_value=WIDTH),
        patch(f"{_MODULE}.build_vector_store", return_value=_FakeVectorStore([])) as build_vector_store,
    ):
        DefaultPartitionRepairService.repair(BUCKET)

    build_vector_store.assert_called_once_with(DB, WIDTH)


def test_stranded_nodes_are_copied_before_they_are_deleted() -> None:
    """Copy first: an interruption must leave a duplicate, never a gap."""
    vector_store = _FakeVectorStore([_key("c1"), _key("c2")])

    report = _repair(vector_store)

    assert vector_store.calls == [
        ("ensure_partitions",),
        ("restore", {NAMESPACE: ["c1", "c2"]}),
        ("delete", ["c1", "c2"]),
    ]
    assert report.moved_nodes == 2
    assert report.document_ids == ["doc1"]


def test_every_stranded_document_is_restored_in_one_call_so_the_collection_is_flushed_once() -> None:
    """Milvus allows a collection one flush every 10 s; a restore per document would stretch a repair into hours."""
    vector_store = _FakeVectorStore(
        [
            _key("c1"),
            _key("s1", NODE_TYPE_SUMMARY),
            _key("c2", document_id="doc2"),
            _key("f1", document_id="doc3", namespace="finance"),
        ]
    )

    report = _repair(vector_store)

    assert vector_store.calls == [
        ("ensure_partitions",),
        ("restore", {NAMESPACE: ["c1", "c2", "s1"], "finance": ["f1"]}),
        ("delete", ["c1", "c2", "f1", "s1"]),
    ]
    assert report.moved_nodes == 4
    assert report.document_ids == ["doc1", "doc2", "doc3"]


def test_summaries_stranded_next_to_content_already_in_place_are_moved_not_deleted() -> None:
    """The nodes and summary runs are separate processes; only the summary run may have landed in _default."""
    vector_store = _FakeVectorStore(
        stranded=[_key("c1"), _key("s1", NODE_TYPE_SUMMARY)],
        present=[_key("c1")],
    )

    report = _repair(vector_store)

    assert vector_store.calls[1:] == [("restore", {NAMESPACE: ["s1"]}), ("delete", ["c1", "s1"])]
    assert report.moved_nodes == 1
    assert vector_store.stranded == []


def test_stranded_copies_superseded_by_a_later_ingestion_are_deleted_without_copying() -> None:
    """A re-ingestion writes fresh node ids, so ids the namespace partition has and _default lacks are newer."""
    vector_store = _FakeVectorStore(stranded=[_key("old1"), _key("old2")], present=[_key("new1")])

    report = _repair(vector_store)

    assert vector_store.calls == [("ensure_partitions",), ("delete", ["old1", "old2"])]
    assert report.superseded_nodes == 2
    assert report.moved_nodes == 0


def test_an_interrupted_move_is_completed_rather_than_taken_for_a_newer_ingestion() -> None:
    vector_store = _FakeVectorStore(stranded=[_key("c1"), _key("c2")], present=[_key("c1")])

    report = _repair(vector_store)

    assert vector_store.calls[1:] == [("restore", {NAMESPACE: ["c2"]}), ("delete", ["c1", "c2"])]
    assert report.moved_nodes == 1


def test_a_second_run_finds_nothing_to_do() -> None:
    vector_store = _FakeVectorStore([_key("c1"), _key("s1", NODE_TYPE_SUMMARY), _key("d1", document_id="doc2")])
    _repair(vector_store)
    vector_store.calls.clear()

    report = _repair(vector_store)

    assert vector_store.calls == [("ensure_partitions",)]
    assert not report.changed_anything


def test_a_legacy_collection_is_left_untouched() -> None:
    vector_store = _FakeVectorStore([_key("c1")], state=MilvusPartitionState.LEGACY)

    report = _repair(vector_store)

    assert vector_store.calls == [("ensure_partitions",)]
    assert report.partition_state is MilvusPartitionState.LEGACY
    assert not report.changed_anything
