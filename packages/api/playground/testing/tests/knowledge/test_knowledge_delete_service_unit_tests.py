from unittest.mock import MagicMock, call, patch

import pytest
from fastapi import HTTPException
from mongoengine import DoesNotExist

from swiss_ai_hub.api.routes.knowledge.knowledge_service import KnowledgeService

_SERVICE_MODULE = "swiss_ai_hub.api.routes.knowledge.knowledge_service"

DB = "tenant-db"
NAMESPACE = "my-namespace"
DOCUMENT_ID = "doc-123"
SOURCE = f"s3://my-bucket/{NAMESPACE}/report.pdf"


def _mock_ref_doc(source: str = SOURCE) -> MagicMock:
    ref_doc = MagicMock()
    ref_doc.data.metadata.source = source
    return ref_doc


@pytest.fixture
def vector_store():
    return MagicMock()


@pytest.fixture
def vector_store_factory(vector_store):
    return MagicMock(return_value=vector_store)


@pytest.fixture
def s3_service():
    service = MagicMock()
    service.delete_directory.return_value = 0
    return service


@pytest.fixture
def doc_store():
    return MagicMock()


@pytest.fixture
def delete_mocks(doc_store):
    with (
        patch.object(KnowledgeService, "_ensure_db_exists"),
        patch(f"{_SERVICE_MODULE}.RefDoc") as ref_doc_cls,
        patch(f"{_SERVICE_MODULE}.create_mongo_document_store", return_value=doc_store) as create_doc_store,
        patch(f"{_SERVICE_MODULE}.get_partition_name_for_namespace", return_value="partition_x") as partition_fn,
    ):
        ref_doc_cls.by_id_and_namespace.return_value = _mock_ref_doc()
        yield ref_doc_cls, create_doc_store, partition_fn


class TestDeleteDocument:
    def test_deletes_from_all_three_layers(self, delete_mocks, doc_store, s3_service, vector_store, vector_store_factory):
        KnowledgeService.delete_document(DB, NAMESPACE, DOCUMENT_ID, s3_service, vector_store_factory)

        vector_store_factory.assert_called_once_with(DB)
        vector_store.delete.assert_called_once_with(DOCUMENT_ID, partition_name="partition_x")
        doc_store.delete_document.assert_called_once_with(DOCUMENT_ID, raise_error=False)
        s3_service.delete_file.assert_called_once_with(container="my-bucket", file_path=f"{NAMESPACE}/report.pdf")

    def test_deletes_figures_folder(self, delete_mocks, s3_service, vector_store_factory):
        KnowledgeService.delete_document(DB, NAMESPACE, DOCUMENT_ID, s3_service, vector_store_factory)

        s3_service.delete_directory.assert_called_once()
        prefix = s3_service.delete_directory.call_args.kwargs["prefix"]
        assert prefix.startswith(f"{NAMESPACE}/")
        assert prefix.endswith("/")

    def test_unknown_document_raises_404(self, delete_mocks, s3_service, vector_store, vector_store_factory):
        ref_doc_cls, _, _ = delete_mocks
        ref_doc_cls.by_id_and_namespace.side_effect = DoesNotExist()

        with pytest.raises(HTTPException) as exc_info:
            KnowledgeService.delete_document(DB, NAMESPACE, DOCUMENT_ID, s3_service, vector_store_factory)

        assert exc_info.value.status_code == 404
        vector_store.delete.assert_not_called()
        s3_service.delete_file.assert_not_called()

    def test_vector_store_failure_stops_before_doc_store_and_s3(
        self, delete_mocks, doc_store, s3_service, vector_store, vector_store_factory
    ):
        vector_store.delete.side_effect = RuntimeError("milvus down")

        with pytest.raises(RuntimeError):
            KnowledgeService.delete_document(DB, NAMESPACE, DOCUMENT_ID, s3_service, vector_store_factory)

        doc_store.delete_document.assert_not_called()
        s3_service.delete_file.assert_not_called()

    def test_s3_failure_propagates(self, delete_mocks, doc_store, s3_service, vector_store_factory):
        s3_service.delete_file.side_effect = RuntimeError("s3 down")

        with pytest.raises(RuntimeError):
            KnowledgeService.delete_document(DB, NAMESPACE, DOCUMENT_ID, s3_service, vector_store_factory)

        doc_store.delete_document.assert_called_once()


class TestBatchDeleteDocuments:
    def test_mixed_ids_yield_per_document_results(self, delete_mocks, s3_service, vector_store_factory):
        ref_doc_cls, _, _ = delete_mocks
        ref_doc_cls.by_id_and_namespace.side_effect = [_mock_ref_doc(), DoesNotExist(), _mock_ref_doc()]

        response = KnowledgeService.batch_delete_documents(
            DB, NAMESPACE, ["doc-1", "doc-2", "doc-3"], s3_service, vector_store_factory
        )

        statuses = {result.document_id: result.status for result in response.results}
        assert statuses == {"doc-1": "deleted", "doc-2": "not_found", "doc-3": "deleted"}

    def test_unexpected_failure_marks_document_failed_and_continues(
        self, delete_mocks, s3_service, vector_store, vector_store_factory
    ):
        vector_store.delete.side_effect = [RuntimeError("milvus down"), None]

        response = KnowledgeService.batch_delete_documents(
            DB, NAMESPACE, ["doc-1", "doc-2"], s3_service, vector_store_factory
        )

        statuses = [result.status for result in response.results]
        assert statuses == ["failed", "deleted"]

    def test_empty_list_returns_empty_results(self, delete_mocks, s3_service, vector_store_factory):
        response = KnowledgeService.batch_delete_documents(DB, NAMESPACE, [], s3_service, vector_store_factory)

        assert response.results == []


class TestDeleteSourceFromDataLake:
    def test_parses_s3_source_into_container_and_key(self, s3_service):
        KnowledgeService._delete_source_from_data_lake(s3_service, SOURCE)

        s3_service.delete_file.assert_called_once_with(container="my-bucket", file_path=f"{NAMESPACE}/report.pdf")

    def test_source_without_object_key_is_skipped(self, s3_service):
        KnowledgeService._delete_source_from_data_lake(s3_service, "s3://my-bucket")

        s3_service.delete_file.assert_not_called()
        s3_service.delete_directory.assert_not_called()
