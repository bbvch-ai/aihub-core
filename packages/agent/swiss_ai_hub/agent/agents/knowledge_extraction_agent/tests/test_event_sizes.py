"""No event an extraction publishes grows with its rows.

An oversized event is dropped by the broker without an error, and the join or the chat then waits forever. Rows and
tables travel by reference (`ExtractionFileStore`), so every event stays small whatever a document yields. The sizes
are checked the way events are serialized, with the worst content: a thousand documents, half of them failing, twenty
columns of whole clauses full of quotes, pipes, backslashes and umlauts, and many rows per document.
"""

import contextlib
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import RecordsExtractedEvent
from swiss_ai_hub.core.generative_ai import (
    BucketNamespacePair,
    ExtractedTableFile,
    ExtractionFileStore,
    KnowledgeDocumentSummary,
    RecordField,
    RecordSchema,
)

from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_answer import ExtractionAnswer
from swiss_ai_hub.agent.capabilities.record_extraction.document_extracted_event import DocumentExtractedEvent
from swiss_ai_hub.agent.capabilities.record_extraction.document_extraction_requested_event import (
    DocumentExtractionRequestedEvent,
)
from swiss_ai_hub.agent.capabilities.record_extraction.document_record_extraction import DocumentRecordExtraction
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_run import ExtractionRun
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_table import ExtractionTable
from swiss_ai_hub.agent.i18n.agent_locale_handler import AgentLocaleHandler

# Well below the development broker's 1 MB `max_payload`: headers and the subject need room, and an answer carries the
# preview twice.
EVENT_LIMIT_BYTES = 400_000
T = AgentLocaleHandler("de")
FIELDS = [f"feld_{index}" for index in range(20)]
SCHEMA = RecordSchema(fields=[RecordField(name=name, type="string", description="Ein Feld.") for name in FIELDS])
CLAUSE = ('Kündigung "fristlos" | Gerät \\ Prüfung Ä ö ü ß ' * 100)[:2000]
COLLECTION = BucketNamespacePair(bucket_name="lieferanten-verträge", namespace_name="verträge")
DOCUMENTS = 1000
ROWS_PER_DOCUMENT = 40


def _size(event: Any) -> int:
    return len(event.model_dump_json(serialize_as_any=True).encode())


def _run() -> ExtractionRun:
    return ExtractionRun(
        extraction_id="x1",
        file_count=DOCUMENTS,
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


class _Store:
    """`ExtractionFileStore` in memory, keeping rows by key and counting the table's rows without encoding them."""

    def __init__(self) -> None:
        self.stored: dict[str, list[dict[str, Any]]] = {}

    async def put_rows(self, extraction_id: str, request_id: str, rows: list[dict[str, Any]]) -> str:
        key = f"record-extraction/{extraction_id}/rows/{request_id}.json"
        self.stored[key] = rows
        return key

    async def rows(self, key: str) -> list[dict[str, Any]]:
        return self.stored[key]

    async def put_table(
        self, extraction_id: str, filename: str, columns: list[str], rows: list[list[Any]]
    ) -> ExtractedTableFile:
        return ExtractedTableFile(
            bucket="agent-files",
            key=f"record-extraction/{extraction_id}/{filename}",
            filename=filename,
            size=len(rows) * 50_000,
            row_count=len(rows),
        )

    @contextlib.contextmanager
    def patched(self) -> Iterator["_Store"]:
        with (
            patch.object(ExtractionFileStore, "put_rows", AsyncMock(side_effect=self.put_rows)),
            patch.object(ExtractionFileStore, "rows", AsyncMock(side_effect=self.rows)),
            patch.object(ExtractionFileStore, "put_table", AsyncMock(side_effect=self.put_table)),
        ):
            yield self


async def _extracted(index: int, rows_per_document: int) -> DocumentExtractedEvent:
    request = _request(index)
    if index % 2:
        return DocumentRecordExtraction._failed(request, "Fehler bei der Prüfung: " + "ü" * 400)
    return await DocumentRecordExtraction._stored(request, [dict.fromkeys(FIELDS, CLAUSE)] * rows_per_document, False)


async def _table(rows_per_document: int) -> tuple[list[DocumentExtractedEvent], RecordsExtractedEvent]:
    with _Store().patched():
        results = [await _extracted(index, rows_per_document) for index in range(DOCUMENTS)]
        return results, await ExtractionTable.assemble(_run(), results, T)


@pytest.mark.asyncio
async def test_a_documents_result_stays_small_however_many_rows_it_yielded():
    with _Store().patched():
        few, many = await _extracted(0, 1), await _extracted(0, ROWS_PER_DOCUMENT * 10)
        failed = await _extracted(1, ROWS_PER_DOCUMENT)

    assert (few.row_count, many.row_count) == (1, 400)
    assert max(_size(few), _size(many), _size(failed)) < EVENT_LIMIT_BYTES
    assert abs(_size(many) - _size(few)) < 10


@pytest.mark.asyncio
async def test_the_table_and_the_blueprints_answer_stay_small_however_many_rows_were_found():
    results, table = await _table(ROWS_PER_DOCUMENT)
    _, small = await _table(1)
    displayer = MagicMock(spec=EventDisplayer)
    displayer.display_chunk = AsyncMock()

    completion = await ExtractionAnswer.table(table, "Kündigungsfristen aller Verträge? " * 50, displayer)

    assert all(_size(result) < EVENT_LIMIT_BYTES for result in results)
    assert table.failed_count == DOCUMENTS // 2
    assert table.total_row_count == DOCUMENTS // 2 * ROWS_PER_DOCUMENT
    assert 0 < table.row_count < table.total_row_count
    assert table.file is not None
    assert table.file.row_count == table.total_row_count
    assert "weitere Dateien" in table.summary
    assert not table.summary.endswith("…")
    assert _size(table) < EVENT_LIMIT_BYTES
    assert abs(_size(table) - _size(small)) < 200
    chunks = [call.args[0] for call in displayer.display_chunk.await_args_list]
    assert len(chunks) >= 2
    assert all(ExtractionTable.serialized_bytes(chunk) < EVENT_LIMIT_BYTES // 2 for chunk in chunks)
    assert _size(completion) < EVENT_LIMIT_BYTES
