"""Events an extraction stored before document summaries named their collection still load and replay.

The dispatcher replays a run's history from JetStream and the API reads persisted events, so a summary written by an
earlier release, without `collection_name`, must validate; otherwise every such event fails on startup and a run
spanning the deploy never finishes.
"""

import json
from typing import Any

from swiss_ai_hub.core.events import BaseEvent
from swiss_ai_hub.core.generative_ai import (
    BucketNamespacePair,
    KnowledgeDocumentListing,
    KnowledgeDocumentSummary,
    RecordField,
    RecordSchema,
)

from swiss_ai_hub.agent.capabilities.record_extraction.document_extracted_event import DocumentExtractedEvent
from swiss_ai_hub.agent.capabilities.record_extraction.document_extraction_requested_event import (
    DocumentExtractionRequestedEvent,
)
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_run import ExtractionRun
from swiss_ai_hub.agent.capabilities.record_extraction.selection_facets import SelectionFacets
from swiss_ai_hub.agent.capabilities.record_extraction.written_location import WrittenLocation
from swiss_ai_hub.agent.i18n.agent_locale_handler import AgentLocaleHandler

# A summary exactly as the release before collection names serialised it.
STORED_SUMMARY: dict[str, Any] = {
    "id": "6650f1c2a1b2c3d4e5f60718",
    "collection": {"bucket_name": "finance-bucket", "namespace_name": "invoices"},
    "path": "2025/hooli-0001.pdf",
    "filename": "hooli-0001.pdf",
    "title": "Hooli invoice 0001",
    "file_type": "pdf",
    "number_of_pages": 2,
    "updated_at": "2025-01-01T00:00:00Z",
    "document_type": "invoice",
    "document_types": ["invoice"],
    "document_attributes": {"document_issuer": "Hooli AG"},
}
SCHEMA = RecordSchema(fields=[RecordField(name="amount", type="number", description="The amount.")])
RUN = ExtractionRun(extraction_id="x1", file_count=1, field_names=["amount"])


def _stored(event: BaseEvent) -> dict[str, Any]:
    """The event as the store holds it, with the document as the earlier release wrote it."""
    stored = json.loads(event.model_dump_json(serialize_as_any=True))
    stored["document"] = STORED_SUMMARY
    return stored


def _current_summary() -> KnowledgeDocumentSummary:
    return KnowledgeDocumentSummary.model_validate({**STORED_SUMMARY, "collection_name": "finance/invoices"})


def test_a_stored_summary_without_a_collection_name_loads_without_one():
    summary = KnowledgeDocumentSummary.model_validate(STORED_SUMMARY)

    assert summary.collection_name is None
    assert summary.collection == BucketNamespacePair(bucket_name="finance-bucket", namespace_name="invoices")


def test_a_stored_document_extracted_event_replays():
    event = DocumentExtractedEvent(
        run=RUN, request_event_id="request-1", document=_current_summary(), rows_key="rows/1.json", row_count=3
    )

    replayed = BaseEvent.deserialize_event(json.dumps(_stored(event)))

    assert isinstance(replayed, DocumentExtractedEvent)
    assert replayed.document.path == "2025/hooli-0001.pdf"
    assert replayed.document.collection_name is None
    assert replayed.row_count == 3


def test_a_stored_document_extraction_request_replays():
    event = DocumentExtractionRequestedEvent(run=RUN, document=_current_summary(), record_schema=SCHEMA)

    replayed = BaseEvent.deserialize_event(_stored(event))

    assert isinstance(replayed, DocumentExtractionRequestedEvent)
    assert replayed.document.collection_name is None


def test_a_summary_without_a_collection_name_is_never_named_nor_matched_as_a_collection():
    old = KnowledgeDocumentSummary.model_validate(STORED_SUMMARY)
    listing = KnowledgeDocumentListing.from_summaries([old, _current_summary()])

    assert listing.in_collection("finance/invoices").documents == [_current_summary()]
    assert SelectionFacets.collections(listing.documents) == ""
    assert not any("None" in line for line in SelectionFacets.lines(listing.documents, AgentLocaleHandler("en")))
    assert WrittenLocation.criteria("finance/invoices", listing)[0].collection == "finance/invoices"
