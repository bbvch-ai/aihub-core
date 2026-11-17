"""Requesting classification of a database's documents marks the request for the pipeline's backfill (#2484)."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from mongoengine import DoesNotExist
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.persistence.rag.datalake.entities import IngestorType

from swiss_ai_hub.api.routes.knowledge.knowledge_service import KnowledgeService

_SERVICE_MODULE = "swiss_ai_hub.api.routes.knowledge.knowledge_service"
DATABASE = "invoices"


def _bucket(**overrides) -> MagicMock:
    defaults = dict(
        id="bucket-1",
        bucket_name=DATABASE,
        db_name=DATABASE,
        deleting=False,
        ingestor=IngestorType.DOCUMENT_INGESTION.value,
        configuration={},
        classification_requested_at=None,
    )
    defaults.update(overrides)
    return MagicMock(**defaults)


def _request(bucket: MagicMock | Exception):
    with (
        patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls,
        patch.object(KnowledgeService, "_database_response", return_value="response") as database_response,
    ):
        if isinstance(bucket, Exception):
            bucket_cls.get_bucket_by_db_name.side_effect = bucket
        else:
            bucket_cls.get_bucket_by_db_name.return_value = bucket
        result = KnowledgeService.request_classification(DATABASE, LocaleHandler("en"))
    return result, bucket_cls, database_response


class TestRequestClassification:
    def test_the_request_is_marked_on_the_database_and_the_database_returned(self):
        result, bucket_cls, database_response = _request(_bucket())

        bucket_cls.request_classification.assert_called_once_with("bucket-1")
        database_response.assert_called_once()
        assert result == "response"

    @pytest.mark.parametrize("bucket", [DoesNotExist(), _bucket(deleting=True)], ids=["missing", "deleting"])
    def test_a_missing_or_deleted_database_is_not_found(self, bucket):
        with pytest.raises(HTTPException) as exc_info:
            _request(bucket)

        assert exc_info.value.status_code == 404

    @pytest.mark.parametrize(
        "bucket",
        [
            _bucket(ingestor=IngestorType.DEFAULT_RAG.value),
            _bucket(ingestor=IngestorType.UNASSIGNED.value),
            _bucket(configuration={"with_document_classification": False}),
        ],
        ids=["legacy", "unassigned", "switched-off"],
    )
    def test_a_database_whose_pipeline_does_not_classify_is_refused(self, bucket):
        with pytest.raises(HTTPException) as exc_info:
            _request(bucket)

        assert exc_info.value.status_code == 409


class TestClassificationAvailable:
    @pytest.mark.parametrize(
        ("bucket", "available"),
        [
            (_bucket(), True),
            (_bucket(configuration={"with_document_classification": True}), True),
            (_bucket(configuration={"with_document_classification": False}), False),
            (_bucket(ingestor="acme_ocr"), True),
            (_bucket(ingestor=IngestorType.SHARED_RAG.value), False),
        ],
        ids=["default", "on", "off", "custom-pipeline", "legacy"],
    )
    def test_availability_follows_the_pipeline_and_the_database_setting(self, bucket, available):
        assert KnowledgeService._is_classification_available(bucket) is available


def test_the_listing_shows_whether_a_request_is_pending():
    requested_at = datetime(2026, 11, 17, 9, 30)
    bucket = _bucket(classification_requested_at=requested_at, source=None)

    with (
        patch.object(KnowledgeService, "_masked_source_configuration", return_value={}),
        patch.object(KnowledgeService, "_safe_extract_locale_string", return_value="Invoices"),
    ):
        response = KnowledgeService._database_response(bucket, LocaleHandler("en"))

    assert response.classification_available is True
    assert response.classification_requested_at == requested_at.replace(tzinfo=UTC)
