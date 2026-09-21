from unittest.mock import MagicMock, patch

import pytest

from swiss_ai_hub.api.routes.knowledge.knowledge_service import KnowledgeService

_SERVICE_MODULE = "swiss_ai_hub.api.routes.knowledge.knowledge_service"

DB = "tenant-db"
NAMESPACE = "my-namespace"
DOCUMENT_ID = "doc-123"
SOURCE = f"s3://my-bucket/{NAMESPACE}/report.pdf"


@pytest.fixture
def s3_service():
    service = MagicMock()
    service.generate_sas_url.return_value = "https://public/signed"
    return service


@pytest.fixture
def url_mocks():
    ref_doc = MagicMock()
    ref_doc.data.metadata.source = SOURCE
    with (
        patch.object(KnowledgeService, "_ensure_db_exists"),
        patch(f"{_SERVICE_MODULE}.RefDoc") as ref_doc_cls,
    ):
        ref_doc_cls.by_id_and_namespace.return_value = ref_doc
        yield ref_doc_cls


class TestGetDocumentUrl:
    def test_preview_url_has_no_disposition(self, url_mocks, s3_service):
        KnowledgeService.get_document_url(DB, NAMESPACE, DOCUMENT_ID, s3_service)

        s3_service.generate_sas_url.assert_called_once_with(
            "my-bucket", f"{NAMESPACE}/report.pdf", response_content_disposition=None
        )

    def test_attachment_url_forces_download_with_filename(self, url_mocks, s3_service):
        KnowledgeService.get_document_url(DB, NAMESPACE, DOCUMENT_ID, s3_service, as_attachment=True)

        s3_service.generate_sas_url.assert_called_once_with(
            "my-bucket", f"{NAMESPACE}/report.pdf", response_content_disposition='attachment; filename="report.pdf"'
        )
