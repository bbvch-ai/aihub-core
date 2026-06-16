from unittest.mock import AsyncMock, MagicMock, patch

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
def nc():
    return MagicMock()


@pytest.fixture
def s3_service():
    service = MagicMock()
    service.delete_directory.return_value = 0
    return service


@pytest.fixture
def delete_mocks():
    with (
        patch.object(KnowledgeService, "_ensure_db_exists"),
        patch.object(KnowledgeService, "_publish_source_updated_event", new_callable=AsyncMock) as publish_event,
        patch(f"{_SERVICE_MODULE}.RefDoc") as ref_doc_cls,
    ):
        ref_doc_cls.by_id_and_namespace.return_value = _mock_ref_doc()
        yield ref_doc_cls, publish_event


class TestDeleteDocument:
    @pytest.mark.asyncio
    async def test_deletes_source_file_and_publishes_event(self, delete_mocks, nc, s3_service):
        _, publish_event = delete_mocks

        await KnowledgeService.delete_document(nc, DB, NAMESPACE, DOCUMENT_ID, s3_service)

        s3_service.delete_file.assert_called_once_with(container="my-bucket", file_path=f"{NAMESPACE}/report.pdf")
        publish_event.assert_awaited_once_with(
            nc=nc, database=DB, container="my-bucket", file_path=f"{NAMESPACE}/report.pdf"
        )

    @pytest.mark.asyncio
    async def test_deletes_figures_folder(self, delete_mocks, nc, s3_service):
        await KnowledgeService.delete_document(nc, DB, NAMESPACE, DOCUMENT_ID, s3_service)

        s3_service.delete_directory.assert_called_once()
        prefix = s3_service.delete_directory.call_args.kwargs["prefix"]
        assert prefix.startswith(f"{NAMESPACE}/")
        assert prefix.endswith("/")

    @pytest.mark.asyncio
    async def test_unknown_document_raises_404(self, delete_mocks, nc, s3_service):
        ref_doc_cls, publish_event = delete_mocks
        ref_doc_cls.by_id_and_namespace.side_effect = DoesNotExist()

        with pytest.raises(HTTPException) as exc_info:
            await KnowledgeService.delete_document(nc, DB, NAMESPACE, DOCUMENT_ID, s3_service)

        assert exc_info.value.status_code == 404
        s3_service.delete_file.assert_not_called()
        publish_event.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_s3_failure_propagates_without_publishing_event(self, delete_mocks, nc, s3_service):
        _, publish_event = delete_mocks
        s3_service.delete_file.side_effect = RuntimeError("s3 down")

        with pytest.raises(RuntimeError):
            await KnowledgeService.delete_document(nc, DB, NAMESPACE, DOCUMENT_ID, s3_service)

        publish_event.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_s3_delete_happens_before_event_publish(self, delete_mocks, nc, s3_service):
        _, publish_event = delete_mocks
        order: list[str] = []
        s3_service.delete_file.side_effect = lambda **_: order.append("s3")
        publish_event.side_effect = lambda **_: order.append("event")

        await KnowledgeService.delete_document(nc, DB, NAMESPACE, DOCUMENT_ID, s3_service)

        assert order == ["s3", "event"]


class TestBatchDeleteDocuments:
    @pytest.mark.asyncio
    async def test_mixed_ids_yield_per_document_results(self, delete_mocks, nc, s3_service):
        ref_doc_cls, _ = delete_mocks
        ref_doc_cls.by_id_and_namespace.side_effect = [_mock_ref_doc(), DoesNotExist(), _mock_ref_doc()]

        response = await KnowledgeService.batch_delete_documents(
            nc, DB, NAMESPACE, ["doc-1", "doc-2", "doc-3"], s3_service
        )

        statuses = {result.document_id: result.status for result in response.results}
        assert statuses == {"doc-1": "scheduled", "doc-2": "not_found", "doc-3": "scheduled"}

    @pytest.mark.asyncio
    async def test_unexpected_failure_marks_document_failed_and_continues(self, delete_mocks, nc, s3_service):
        s3_service.delete_file.side_effect = [RuntimeError("s3 down"), None]

        response = await KnowledgeService.batch_delete_documents(nc, DB, NAMESPACE, ["doc-1", "doc-2"], s3_service)

        statuses = [result.status for result in response.results]
        assert statuses == ["failed", "scheduled"]

    @pytest.mark.asyncio
    async def test_empty_list_returns_empty_results(self, delete_mocks, nc, s3_service):
        response = await KnowledgeService.batch_delete_documents(nc, DB, NAMESPACE, [], s3_service)

        assert response.results == []


class TestDeleteSourceFromDataLake:
    def test_parses_s3_source_into_container_and_key(self, s3_service):
        container, file_path = KnowledgeService._delete_source_from_data_lake(s3_service, SOURCE)

        assert (container, file_path) == ("my-bucket", f"{NAMESPACE}/report.pdf")
        s3_service.delete_file.assert_called_once_with(container="my-bucket", file_path=f"{NAMESPACE}/report.pdf")

    def test_source_without_object_key_raises_500(self, s3_service):
        with pytest.raises(HTTPException) as exc_info:
            KnowledgeService._delete_source_from_data_lake(s3_service, "s3://my-bucket")

        assert exc_info.value.status_code == 500
        s3_service.delete_file.assert_not_called()

    def test_non_s3_source_raises_500(self, s3_service):
        with pytest.raises(HTTPException) as exc_info:
            KnowledgeService._delete_source_from_data_lake(s3_service, "file:///etc/passwd")

        assert exc_info.value.status_code == 500
        s3_service.delete_file.assert_not_called()
