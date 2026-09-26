from contextlib import ExitStack
from unittest.mock import MagicMock, patch

from dagster import ExecuteInProcessResult
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import NAMESPACE, SOURCE

from swiss_ai_hub.pipeline.ops.document.delete_removed_ref_docs_from_docstore import (
    delete_removed_ref_docs_from_docstore,
)
from swiss_ai_hub.pipeline.util.run_routing import BUCKET_RUN_TAG

BUCKET = "researchdocs"
DB_NAME = "researchdocs_db"

_FIGURES = "swiss_ai_hub.pipeline.ops.document.delete_figures_for_many_ref_doc"
_DOCSTORE = "swiss_ai_hub.pipeline.ops.document.delete_many_ref_doc_from_docstore"
_VECTORS = "swiss_ai_hub.pipeline.ops.nodes.delete_many_nodes_from_vector_store"
_REF_DOCS = "swiss_ai_hub.pipeline.ops.data_lake.fetch_ref_docs_to_remove"


class _Stores:
    """The removal chain's stores, shared across runs the way the real doc store outlives a failed run."""

    def __init__(self) -> None:
        self.records: dict[str, dict] = {"doc1": {SOURCE: f"s3://{BUCKET}/reports/a.pdf", NAMESPACE: "reports"}}
        self.vector_store = MagicMock()
        self.data_lake_client = MagicMock()
        self.data_lake_client.directory_exists.return_value = True
        self.data_lake_client.list_directory_contents.return_value = []
        self.doc_store = MagicMock()
        self.doc_store.delete_document.side_effect = lambda doc_id, raise_error: self.records.pop(doc_id, None)

    def remaining_records(self) -> list[MagicMock]:
        return [self._record(doc_id, metadata) for doc_id, metadata in self.records.items()]

    @staticmethod
    def _record(doc_id: str, metadata: dict) -> MagicMock:
        record = MagicMock()
        record.id = doc_id
        record.data.text = "body"
        record.data.metadata.to_mongo.return_value.to_dict.return_value = metadata
        return record

    def run_removal(self) -> ExecuteInProcessResult:
        with ExitStack() as stack:
            for module in (_REF_DOCS, _VECTORS, _DOCSTORE):
                stack.enter_context(patch(f"{module}.get_db_name_from_bucket_name", return_value=DB_NAME))
            stack.enter_context(patch(f"{_REF_DOCS}.MongoConnectionRegistry"))
            ref_doc_entity = stack.enter_context(patch(f"{_REF_DOCS}.RefDoc"))
            ref_doc_entity.get_documents.side_effect = lambda **_: self.remaining_records()
            stack.enter_context(patch(f"{_VECTORS}.build_vector_store", return_value=self.vector_store))
            stack.enter_context(patch(f"{_FIGURES}.build_s3_data_lake_client", return_value=self.data_lake_client))
            stack.enter_context(patch(f"{_DOCSTORE}.build_doc_store", return_value=self.doc_store))

            return delete_removed_ref_docs_from_docstore.to_job().execute_in_process(
                input_values={"data_lake_files": []},
                tags={BUCKET_RUN_TAG: BUCKET},
                raise_on_error=False,
            )


class TestRemovalKeepsTheRecordUntilEveryOtherStoreIsClean:
    """#1925: the record is the only marker of pending work, so it must outlive a failed vector delete."""

    def test_a_failed_vector_delete_leaves_figures_and_record_in_place(self):
        stores = _Stores()
        stores.vector_store.delete_documents.side_effect = RuntimeError("milvus unavailable")

        result = stores.run_removal()

        assert not result.success
        stores.data_lake_client.delete_directory.assert_not_called()
        stores.doc_store.delete_document.assert_not_called()
        assert "doc1" in stores.records

    def test_the_next_run_retries_from_the_record_and_deletes_everything_once(self):
        stores = _Stores()
        stores.vector_store.delete_documents.side_effect = [RuntimeError("milvus unavailable"), 3]
        stores.run_removal()

        result = stores.run_removal()

        assert result.success
        assert stores.vector_store.delete_documents.call_count == 2
        stores.vector_store.delete_documents.assert_called_with(["doc1"], ["reports"])
        stores.data_lake_client.delete_directory.assert_called_once()
        stores.doc_store.delete_document.assert_called_once_with("doc1", raise_error=False)
        assert stores.records == {}

    def test_a_run_after_a_successful_removal_has_nothing_left_to_do(self):
        stores = _Stores()
        stores.vector_store.delete_documents.return_value = 3
        stores.run_removal()

        result = stores.run_removal()

        assert result.success
        stores.vector_store.delete_documents.assert_called_once()
        stores.doc_store.delete_document.assert_called_once()
