"""A document whose ingestion failed is told apart from one still being processed."""

from unittest.mock import MagicMock

import pytest

from swiss_ai_hub.api.routes.knowledge.dto.document_dto import DocumentDTO
from swiss_ai_hub.api.routes.knowledge.dto.document_ingestion_state import DocumentIngestionState


def _ref_doc(*, is_ingested: bool | None, failed_attempts: int | None = None, gave_up: bool | None = None) -> MagicMock:
    ref_doc = MagicMock()
    ref_doc.id = "doc-1"
    ref_doc.data.text = ""
    metadata = ref_doc.data.metadata
    metadata.source = "s3://bucket/finance/q3.pdf"
    metadata.namespace = "finance"
    metadata.number_of_pages = None
    metadata.document_title = "q3.pdf"
    metadata.created_at = 1_700_000_000
    metadata.updated_at = 1_700_000_000
    metadata.inserted_at = 1_700_000_000
    metadata.is_ingested = is_ingested
    metadata.ingestion_failed_attempts = failed_attempts
    metadata.ingestion_gave_up = gave_up
    return ref_doc


@pytest.mark.parametrize(
    ("is_ingested", "failed_attempts", "gave_up", "state", "attempts"),
    [
        (True, None, None, DocumentIngestionState.INGESTED, None),
        (None, None, None, DocumentIngestionState.INGESTED, None),
        (False, None, None, DocumentIngestionState.PROCESSING, None),
        (False, 2, False, DocumentIngestionState.RETRYING, 2),
        (False, 4, True, DocumentIngestionState.FAILED, 4),
    ],
    ids=["ingested", "legacy-without-flag", "processing", "retrying", "failed"],
)
def test_the_ingestion_state_follows_the_record(
    is_ingested: bool | None,
    failed_attempts: int | None,
    gave_up: bool | None,
    state: DocumentIngestionState,
    attempts: int | None,
) -> None:
    dto = DocumentDTO.from_ref_doc(_ref_doc(is_ingested=is_ingested, failed_attempts=failed_attempts, gave_up=gave_up))

    assert dto.ingestion_state is state
    assert dto.ingestion_failed_attempts == attempts


def test_an_ingested_document_never_shows_an_old_failure() -> None:
    """mark_ingested clears the failure, but a record written in between must still read as ingested."""
    dto = DocumentDTO.from_ref_doc(_ref_doc(is_ingested=True, failed_attempts=3, gave_up=True))

    assert dto.ingestion_state is DocumentIngestionState.INGESTED
    assert dto.ingestion_failed_attempts is None
