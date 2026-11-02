from contextlib import ExitStack
from unittest.mock import MagicMock, patch

from swiss_ai_hub.pipeline.services.orphaned_node_repair_service import OrphanedNodeRepairService
from swiss_ai_hub.pipeline.util.id_utils import uri_to_id

_MODULE = "swiss_ai_hub.pipeline.services.orphaned_node_repair_service"

BUCKET = "researchdocs"
DB = "researchdocs_db"
LANDED_URI = f"s3://{BUCKET}/reports/landed.pdf"
LANDED_ID = uri_to_id(LANDED_URI)


class _FakeVectorStore:
    """Holds nodes per partition and records every delete, like a collection with two partitions."""

    def __init__(self, partitions: dict[str, dict[str, list[str]]]) -> None:
        self.partitions = partitions
        self.requested_namespaces: list[str] | None = None
        self.deletes: list[tuple[list[str], str]] = []

    def document_partition_names(self, namespaces: list[str]) -> list[str]:
        self.requested_namespaces = namespaces
        return list(self.partitions)

    def node_ids_by_document(self, partition_name: str) -> dict[str, list[str]]:
        return self.partitions[partition_name]

    def delete_nodes_in_partition(self, node_ids: list[str], partition_name: str) -> int:
        self.deletes.append((node_ids, partition_name))
        return len(node_ids)


def _vector_store() -> _FakeVectorStore:
    return _FakeVectorStore(
        {
            "partition_7": {"live": ["n1", "n2"], "orphan": ["n3"], LANDED_ID: ["n4"]},
            "_default": {"orphan": ["n5", "n6"]},
        }
    )


def _data_lake_file() -> MagicMock:
    data_lake_file = MagicMock()
    data_lake_file.id_ = LANDED_ID
    data_lake_file.namespace = "reports"
    return data_lake_file


def _repair(vector_store: _FakeVectorStore, dry_run: bool, recreated: set[str] | None = None):
    with ExitStack() as stack:
        stack.enter_context(patch(f"{_MODULE}.ensure_main_db_connection"))
        stack.enter_context(patch(f"{_MODULE}.MongoConnectionRegistry"))
        bucket_entity = stack.enter_context(patch(f"{_MODULE}.BucketEntity"))
        bucket_entity.get_bucket_by_bucket_name.return_value.db_name = DB
        bucket_entity.get_bucket_by_bucket_name.return_value.id = "b1"
        namespace_entity = stack.enter_context(patch(f"{_MODULE}.NamespaceEntity"))
        registered = MagicMock()
        registered.namespace_name = "archive"
        namespace_entity.get_namespaces_by_bucket.return_value = [registered]
        ref_doc = stack.enter_context(patch(f"{_MODULE}.RefDoc"))
        ref_doc.get_all_ids.return_value = {"live"}
        ref_doc.get_all_namespaces.return_value = ["reports", "contracts"]
        ref_doc.get_existing_ids.return_value = recreated or set()
        build_client = stack.enter_context(patch(f"{_MODULE}.build_s3_data_lake_client"))
        build_client.return_value.get_all_files.return_value = [_data_lake_file()]
        stack.enter_context(patch(f"{_MODULE}.build_vector_store", return_value=vector_store))

        report = OrphanedNodeRepairService.repair(bucket=BUCKET, dry_run=dry_run)
        return report, ref_doc, namespace_entity


class TestOrphanedNodeRepair:
    def test_deletes_only_nodes_without_a_record_or_a_data_lake_file(self):
        vector_store = _vector_store()

        report, _, _ = _repair(vector_store, dry_run=False)

        assert vector_store.deletes == [(["n3"], "partition_7"), (["n5", "n6"], "_default")]
        assert report.nodes_by_document == {"orphan": 3}
        assert report.orphaned_documents == 1
        assert report.orphaned_nodes == 3
        assert report.deleted_nodes == 3

    def test_scans_the_partitions_of_every_namespace_the_database_knows(self):
        vector_store = _vector_store()

        _, _, namespace_entity = _repair(vector_store, dry_run=True)

        namespace_entity.get_namespaces_by_bucket.assert_called_once_with("b1")
        assert vector_store.requested_namespaces == ["archive", "contracts", "reports"]

    def test_a_dry_run_reports_the_orphans_and_deletes_nothing(self):
        vector_store = _vector_store()

        report, ref_doc, _ = _repair(vector_store, dry_run=True)

        assert vector_store.deletes == []
        ref_doc.get_existing_ids.assert_not_called()
        assert report.orphaned_nodes == 3
        assert report.deleted_nodes == 0

    def test_a_record_created_after_the_scan_keeps_its_nodes(self):
        vector_store = _vector_store()

        report, ref_doc, _ = _repair(vector_store, dry_run=False, recreated={"orphan"})

        ref_doc.get_existing_ids.assert_called_with(DB, ["orphan"])
        assert all(node_ids == [] for node_ids, _ in vector_store.deletes)
        assert report.deleted_nodes == 0
