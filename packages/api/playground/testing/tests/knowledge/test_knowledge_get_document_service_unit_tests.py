from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from mongoengine import DoesNotExist

from swiss_ai_hub.api.routes.knowledge.knowledge_service import KnowledgeService

_SERVICE_MODULE = "swiss_ai_hub.api.routes.knowledge.knowledge_service"

DB = "tenant-db"
NAMESPACE = "my-namespace"
DOCUMENT_ID = "doc-123"
SOURCE = f"s3://my-bucket/{NAMESPACE}/report.pdf"


def _mock_ref_doc() -> MagicMock:
    ref_doc = MagicMock()
    ref_doc.id = DOCUMENT_ID
    ref_doc.data.text = "the parsed document body"
    ref_doc.data.metadata.source = SOURCE
    ref_doc.data.metadata.namespace = NAMESPACE
    ref_doc.data.metadata.number_of_pages = 3
    ref_doc.data.metadata.document_title = "report.pdf"
    ref_doc.data.metadata.is_ingested = True
    ref_doc.data.metadata.created_at = 1_700_000_000
    ref_doc.data.metadata.updated_at = 1_700_000_000
    ref_doc.data.metadata.inserted_at = 1_700_000_000
    return ref_doc


@pytest.fixture
def get_document_mocks():
    with (
        patch.object(KnowledgeService, "_ensure_db_exists"),
        patch(f"{_SERVICE_MODULE}.RefDoc") as ref_doc_cls,
    ):
        ref_doc_cls.by_id_and_namespace.return_value = _mock_ref_doc()
        yield ref_doc_cls


class TestGetDocumentById:
    def test_lookup_is_scoped_to_the_namespace_from_the_route(self, get_document_mocks):
        document = KnowledgeService.get_document_by_id(DB, NAMESPACE, DOCUMENT_ID)

        get_document_mocks.by_id_and_namespace.assert_called_once_with(
            db_alias=DB, doc_id=DOCUMENT_ID, namespace=NAMESPACE
        )
        get_document_mocks.by_id.assert_not_called()
        assert document.id == DOCUMENT_ID
        assert document.namespace == NAMESPACE

    def test_unknown_document_raises_404(self, get_document_mocks):
        get_document_mocks.by_id_and_namespace.side_effect = DoesNotExist()

        with pytest.raises(HTTPException) as exc_info:
            KnowledgeService.get_document_by_id(DB, NAMESPACE, DOCUMENT_ID)

        assert exc_info.value.status_code == 404

    def test_document_of_another_namespace_raises_404(self, get_document_mocks):
        get_document_mocks.by_id_and_namespace.side_effect = DoesNotExist()

        with pytest.raises(HTTPException) as exc_info:
            KnowledgeService.get_document_by_id(DB, "a-namespace-the-caller-may-read", DOCUMENT_ID)

        assert exc_info.value.status_code == 404
