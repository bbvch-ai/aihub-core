"""Every event an extraction publishes stays below the message broker's limit at the profile's maxima.

An oversized event is dropped by the broker without an error, and the join or the chat then waits forever, so the
sizes are checked the way events are serialized, with the worst content a document can yield: the most fields, cells
of a whole clause full of quotes, pipes, backslashes and umlauts, and half of the documents failing.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.generative_ai import BucketNamespacePair, KnowledgeDocumentSummary, RecordField, RecordSchema

from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_answer import ExtractionAnswer
from swiss_ai_hub.agent.capabilities.record_extraction.document_extracted_event import DocumentExtractedEvent
from swiss_ai_hub.agent.capabilities.record_extraction.document_extraction_requested_event import (
    DocumentExtractionRequestedEvent,
)
from swiss_ai_hub.agent.capabilities.record_extraction.document_record_extraction import (
    EVENT_BYTES,
    DocumentRecordExtraction,
)
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_run import ExtractionRun
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_table import ExtractionTable
from swiss_ai_hub.agent.i18n.agent_locale_handler import AgentLocaleHandler

# The development broker's `max_payload` is 1 MB; VMs and Kubernetes allow 2 MB. Headers and the subject need room.
BROKER_BYTES = 900_000
T = AgentLocaleHandler("de")
FIELDS = [f"feld_{index}" for index in range(20)]
SCHEMA = RecordSchema(fields=[RecordField(name=name, type="string", description="Ein Feld.") for name in FIELDS])
CLAUSE = ('Kündigung "fristlos" | Gerät \\ Prüfung Ä ö ü ß ' * 100)[:2000]
COLLECTION = BucketNamespacePair(bucket_name="lieferanten-verträge", namespace_name="verträge")
MAX_FILES = 500
MAX_ROWS = 2000


def _size(event: object) -> int:
    return len(event.model_dump_json(serialize_as_any=True).encode())


def _run() -> ExtractionRun:
    return ExtractionRun(
        extraction_id="x1",
        file_count=MAX_FILES,
        field_names=FIELDS,
        criteria="Pfad passt auf 'verträge/**' und Text enthält 'Kündigungsfrist' " * 15,
        notices=["Ein Hinweis über die Suche, die Grenzen und die Auswahl der Dokumente. " * 5] * 3,
        show_collection=True,
    )


def _document(index: int) -> KnowledgeDocumentSummary:
    path = f"verträge/lieferanten/{'ä' * 40}/vertrag-{index:04d}-{'ü' * 60}.pdf"
    return KnowledgeDocumentSummary(
        id=f"doc-{index}",
        collection=COLLECTION,
        path=path,
        filename=path.rsplit("/", 1)[-1],
        title=path,
        file_type="pdf",
        updated_at=datetime(2025, 1, 1, tzinfo=UTC),
    )


def _request(index: int) -> DocumentExtractionRequestedEvent:
    return DocumentExtractionRequestedEvent(run=_run(), document=_document(index), record_schema=SCHEMA)


def _extracted(index: int) -> DocumentExtractedEvent:
    if index % 2:
        return DocumentRecordExtraction._failed(_request(index), "Fehler bei der Prüfung: " + "ü" * 400)
    return DocumentRecordExtraction._bounded(_request(index), [dict.fromkeys(FIELDS, CLAUSE)] * 40)


def test_a_documents_result_stays_within_its_share_of_the_broker():
    result = _extracted(0)

    assert result.rows_dropped > 0
    assert 0 < len(result.rows) < 40
    assert _size(result) <= EVENT_BYTES


def test_the_table_and_the_blueprints_answer_stay_below_the_broker_limit():
    results = [_extracted(index) for index in range(MAX_FILES)]

    table, _ = ExtractionTable.assemble(_run(), results, MAX_ROWS, T)

    assert table.failed_count == MAX_FILES // 2
    assert table.row_count < table.total_row_count
    assert "weitere Dateien" in table.summary
    assert not table.summary.endswith("…")
    assert _size(table) < BROKER_BYTES


@pytest.mark.asyncio
async def test_the_answer_streams_in_chunks_and_completes_below_the_broker_limit():
    table, _ = ExtractionTable.assemble(_run(), [_extracted(index) for index in range(MAX_FILES)], MAX_ROWS, T)
    displayer = MagicMock(spec=EventDisplayer)
    displayer.display_chunk = AsyncMock()

    completion = await ExtractionAnswer.table(table, "Kündigungsfristen aller Verträge? " * 50, displayer)

    chunks = [call.args[0] for call in displayer.display_chunk.await_args_list]
    assert len(chunks) > 2
    assert all(ExtractionTable.serialized_bytes(chunk) < BROKER_BYTES // 4 for chunk in chunks)
    assert _size(completion) < BROKER_BYTES
