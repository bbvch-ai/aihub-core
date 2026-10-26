"""One table across many knowledge documents: documents are extracted in parallel and joined per extraction, a
document that fails is listed rather than fatal, the table names the file of every row, and rows travel by reference:
each document's rows and the whole table are stored as files, the events carry a key and a preview."""

import asyncio
import contextlib
import functools
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    ExtractRecordsEvent,
    LLMEvent,
    RecordsExtractedEvent,
    RunToolLoopEvent,
    StopEvent,
    ToolCallApprovedEvent,
    ToolCallsDecidedEvent,
    ToolLoopMode,
    ToolLoopState,
    ToolResultEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.generative_ai import (
    BucketNamespacePair,
    DocumentExtractionResult,
    ExtractedTableFile,
    ExtractedTableMarkup,
    ExtractionFileStore,
    KnowledgeDocument,
    KnowledgeDocumentCriteria,
    KnowledgeDocumentSelection,
    KnowledgeDocumentSelectionResult,
    KnowledgeDocumentSummary,
    LLMConfig,
    RecordField,
    RecordProvenance,
    RecordSchema,
)
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.capabilities.conversation.conversation import Conversation
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_collection import (
    KnowledgeDocumentCollection,
)
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_config import KnowledgeDocumentConfig
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_run_scope import (
    KnowledgeDocumentRunScope,
)
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_tools import KnowledgeDocumentTools
from swiss_ai_hub.agent.capabilities.record_extraction.document_extracted_event import DocumentExtractedEvent
from swiss_ai_hub.agent.capabilities.record_extraction.document_extraction_requested_event import (
    DocumentExtractionRequestedEvent,
)
from swiss_ai_hub.agent.capabilities.record_extraction.document_record_extraction import DocumentRecordExtraction
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_planner import ExtractionPlanner
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_run import ExtractionRun
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_table import (
    CELL_CHARACTERS,
    PREVIEW_BYTES,
    PREVIEW_CHARACTERS,
    PREVIEW_ROWS,
    ExtractionTable,
)
from swiss_ai_hub.agent.capabilities.record_extraction.reading_heartbeat import ReadingHeartbeat
from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction import (
    RecordExtraction,
    answers_an_extraction_call,
    every_document_answered,
)
from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction_config import RecordExtractionConfig
from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction_fields import RecordExtractionFields
from swiss_ai_hub.agent.capabilities.record_extraction.record_selection_tools import RecordSelectionTools
from swiss_ai_hub.agent.capabilities.record_extraction.records_tool_result import RecordsToolResult
from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop import ToolLoop
from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop_fields import ToolLoopFields
from swiss_ai_hub.agent.i18n.agent_locale_handler import AgentLocaleHandler
from swiss_ai_hub.agent.workflow.decorators.step import step

T = AgentLocaleHandler("en")
FINANCE = BucketNamespacePair(bucket_name="finance-db", namespace_name="invoices")
LEGAL = BucketNamespacePair(bucket_name="legal-db", namespace_name="contracts")
PLANNER = "swiss_ai_hub.agent.capabilities.record_extraction.extraction_planner"
EXTRACTION = "swiss_ai_hub.agent.capabilities.record_extraction.document_record_extraction"
SCOPE_OF = "swiss_ai_hub.agent.capabilities.record_extraction.record_extraction.KnowledgeDocumentScope.of"
SCHEMA = RecordSchema(
    fields=[
        RecordField(name="item", type="string", description="The billed item."),
        RecordField(name="amount", type="number", description="The amount in CHF."),
    ]
)


class TableConfig(RecordExtractionFields, AgentConfig):
    pass


class _Store:
    """`ExtractionFileStore` in memory: the rows each document stored and every table written."""

    def __init__(self) -> None:
        self.stored_rows: dict[str, list[dict[str, Any]]] = {}
        self.tables: list[tuple[str, str, list[str], list[list[Any]]]] = []
        self.put_rows = AsyncMock(side_effect=self._put_rows)
        self.rows = AsyncMock(side_effect=self._rows)
        self.put_table = AsyncMock(side_effect=self._put_table)

    async def _put_rows(self, extraction_id: str, request_id: str, rows: list[dict[str, Any]]) -> str:
        key = f"record-extraction/{extraction_id}/rows/{request_id}.json"
        self.stored_rows[key] = rows
        return key

    async def _rows(self, key: str) -> list[dict[str, Any]]:
        return self.stored_rows[key]

    async def _put_table(
        self, extraction_id: str, filename: str, columns: list[str], rows: list[list[Any]]
    ) -> ExtractedTableFile:
        self.tables.append((extraction_id, filename, columns, rows))
        return ExtractedTableFile(
            bucket="agent-files",
            key=f"record-extraction/{extraction_id}/{filename}",
            filename=filename,
            size=100,
            row_count=len(rows),
        )

    @contextlib.contextmanager
    def patched(self) -> Iterator["_Store"]:
        with (
            patch.object(ExtractionFileStore, "put_rows", self.put_rows),
            patch.object(ExtractionFileStore, "rows", self.rows),
            patch.object(ExtractionFileStore, "put_table", self.put_table),
        ):
            yield self


@pytest.fixture
def store() -> Iterator[_Store]:
    with _Store().patched() as patched:
        yield patched


def _config(**settings: Any) -> TableConfig:
    return TableConfig(
        agent_id="tables",
        name=LocaleString(en="Tables"),
        description=LocaleString(en="Tables fixture"),
        llm=LLMConfig(model_name="text-generation/main"),
        knowledge_documents=KnowledgeDocumentConfig(enabled=True, path_glob="invoices/**"),
        record_extraction=RecordExtractionConfig(**settings),
    )


def _summary(path: str, collection: BucketNamespacePair = FINANCE) -> KnowledgeDocumentSummary:
    return KnowledgeDocumentSummary(
        id=path.replace("/", "-"),
        collection=collection,
        path=path,
        filename=path.rsplit("/", 1)[-1],
        title=path,
        file_type="pdf",
        updated_at=datetime(2025, 1, 1, tzinfo=UTC),
    )


def _run(extraction_id: str = "x1", file_count: int = 2, **fields: Any) -> ExtractionRun:
    return ExtractionRun(extraction_id=extraction_id, file_count=file_count, field_names=SCHEMA.field_names, **fields)


def _result(
    run: ExtractionRun, path: str, rows: list[dict[str, Any]] | None = None, store: _Store | None = None, **fields: Any
) -> DocumentExtractedEvent:
    """A document's result; its rows are stored in `store`, as the extraction step stores them."""
    request_id = f"req-{run.extraction_id}-{path}"
    rows = rows or []
    stored: dict[str, Any] = {}
    if rows and store is not None:
        key = f"record-extraction/{run.extraction_id}/rows/{request_id}.json"
        store.stored_rows[key] = rows
        unsure = sum(1 for row in rows if row.get(RecordSchema.MATCH_FIELD) == RecordSchema.MATCH_UNSURE)
        stored = {"rows_key": key, "row_count": len(rows), "unsure_count": unsure}
    return DocumentExtractedEvent(run=run, request_event_id=request_id, document=_summary(path), **{**stored, **fields})


def _selection() -> KnowledgeDocumentSelection:
    return KnowledgeDocumentSelection(any_of=[KnowledgeDocumentCriteria(path_glob="invoices/2025/**")])


def _body_lines(table: str) -> list[str]:
    return [line for line in table.splitlines() if line.startswith("|")][2:]


class TestJoin:
    @pytest.mark.asyncio
    async def test_the_join_waits_for_every_document_of_its_extraction(self):
        run = _run()
        first = _result(run, "a.pdf")

        assert not await every_document_answered(first, [first], None)
        second = _result(run, "b.pdf")
        assert await every_document_answered(second, [first, second], None)

    @pytest.mark.asyncio
    async def test_another_extractions_results_do_not_count(self):
        mine, other = _run("x1"), _run("x2")
        first = _result(mine, "a.pdf")
        foreign = [_result(other, "a.pdf"), _result(other, "b.pdf")]

        assert not await every_document_answered(first, [first, *foreign], None)

    @pytest.mark.asyncio
    async def test_a_result_delivered_twice_counts_once(self):
        first = _result(_run(), "a.pdf")

        assert not await every_document_answered(first, [first, first], None)

    @pytest.mark.asyncio
    async def test_an_assembled_extraction_is_not_joined_again(self):
        run = _run()
        results = [_result(run, "a.pdf"), _result(run, "b.pdf")]
        done = RecordsExtractedEvent(extraction_id="x1", summary="done")

        assert not await every_document_answered(results[1], results, [done])


class TestTable:
    @pytest.mark.asyncio
    async def test_every_row_names_its_file_and_the_whole_table_is_stored_as_a_file(self, store: _Store):
        run = _run()
        results = [
            _result(run, "invoices/b.pdf", [{"item": "Laptop", "amount": 900}], store),
            _result(run, "invoices/a.pdf", [{"item": "Rack", "amount": 1200}, {"item": "Cable", "amount": 20}], store),
        ]

        table = await ExtractionTable.assemble(run, results, T)

        assert table.columns == ["Path", "File", "Item", "Amount"]
        assert table.table.startswith('[aihub-extracted-table]: # "rows=3"')
        assert _body_lines(table.table) == [
            "| invoices/a.pdf | a.pdf | Rack | 1200 |",
            "| invoices/a.pdf | a.pdf | Cable | 20 |",
            "| invoices/b.pdf | b.pdf | Laptop | 900 |",
        ]
        assert (table.file_count, table.row_count, table.total_row_count, table.truncated) == (2, 3, 3, False)
        assert store.tables == [
            (
                "x1",
                "table-x1.csv",
                ["Path", "File", "Item", "Amount"],
                [
                    ["invoices/a.pdf", "a.pdf", "Rack", 1200],
                    ["invoices/a.pdf", "a.pdf", "Cable", 20],
                    ["invoices/b.pdf", "b.pdf", "Laptop", 900],
                ],
            )
        ]
        assert table.file is not None
        assert (table.file.filename, table.file.row_count) == ("table-x1.csv", 3)
        assert "**Shown here:**" not in table.summary

    @pytest.mark.asyncio
    async def test_the_preview_shows_at_most_its_rows_and_the_file_holds_every_row(self, store: _Store):
        run = _run(file_count=1)
        rows = [{"item": f"item {index}", "amount": index} for index in range(PREVIEW_ROWS + 50)]

        table = await ExtractionTable.assemble(run, [_result(run, "a.pdf", rows, store)], T)

        assert (table.row_count, table.total_row_count) == (PREVIEW_ROWS, 150)
        assert len(_body_lines(table.table)) == PREVIEW_ROWS
        assert table.table.startswith(f'[aihub-extracted-table]: # "rows={PREVIEW_ROWS}"')
        assert len(store.tables[0][3]) == 150
        assert "**Shown here:** the first 100 of 150 rows; the file holds all of them." in table.summary

    @pytest.mark.asyncio
    async def test_the_preview_stops_at_its_characters(self, store: _Store):
        run = _run(file_count=1)
        rows = [{"item": "x" * 900, "amount": index} for index in range(PREVIEW_ROWS)]

        table = await ExtractionTable.assemble(run, [_result(run, "a.pdf", rows, store)], T)

        assert 0 < table.row_count < PREVIEW_ROWS
        assert sum(len(line) + 1 for line in table.table.splitlines() if line.startswith("|")) <= PREVIEW_CHARACTERS
        assert table.total_row_count == PREVIEW_ROWS
        assert f"the first {table.row_count} of 100 rows" in table.summary

    @pytest.mark.asyncio
    async def test_the_preview_stops_at_its_serialized_bytes(self, store: _Store):
        run = _run(file_count=1)
        rows = [{"item": "ü" * 900, "amount": index} for index in range(PREVIEW_ROWS)]

        table = await ExtractionTable.assemble(run, [_result(run, "a.pdf", rows, store)], T)

        lines = [line for line in table.table.splitlines() if line.startswith("|")]
        assert 0 < table.row_count < PREVIEW_ROWS
        assert sum(ExtractionTable.serialized_bytes(line) for line in lines) <= PREVIEW_BYTES

    @pytest.mark.asyncio
    async def test_a_single_huge_row_is_still_shown(self, store: _Store):
        run = ExtractionRun(extraction_id="x1", file_count=1, field_names=[f"field_{index}" for index in range(200)])
        rows = [{f"field_{index}": "ü" * 2000 for index in range(200)}]

        table = await ExtractionTable.assemble(run, [_result(run, "a.pdf", rows, store)], T)

        assert table.row_count == 1

    @pytest.mark.asyncio
    async def test_long_cells_are_cut_in_the_preview_only(self, store: _Store):
        run = _run(file_count=1)

        table = await ExtractionTable.assemble(
            run, [_result(run, "a.pdf", [{"item": "y" * 2000, "amount": 1}], store)], T
        )

        assert f"| {'y' * (CELL_CHARACTERS - 1)}… | 1 |" in table.table
        assert store.tables[0][3][0][2] == "y" * 2000

    @pytest.mark.asyncio
    async def test_a_document_without_rows_counts_as_extracted_not_failed_and_is_named(self, store: _Store):
        run = _run()
        results = [_result(run, "a.pdf", [{"item": "Rack", "amount": 1}], store), _result(run, "b.pdf")]

        table = await ExtractionTable.assemble(run, results, T)

        assert (table.file_count, table.failed_count, table.row_count) == (2, 0, 1)
        assert "**No rows from:** b.pdf" in table.summary
        store.rows.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_failed_files_are_listed_under_the_table_and_not_as_without_rows(self, store: _Store):
        run = _run(file_count=3)
        results = [
            _result(run, "a.pdf", [{"item": "Rack", "amount": 1}], store),
            _result(run, "b.pdf", failure_reason="boom"),
            _result(run, "c.pdf"),
        ]

        table = await ExtractionTable.assemble(run, results, T)

        assert table.failed_count == 1
        assert "- b.pdf: boom" in table.summary
        assert "**No rows from:** c.pdf\n" in table.summary + "\n"
        assert "b.pdf" not in table.summary.split("**No rows from:**")[1].split("\n")[0]

    @pytest.mark.asyncio
    async def test_without_any_row_there_is_no_file_and_no_preview(self, store: _Store):
        run = _run()

        table = await ExtractionTable.assemble(run, [_result(run, "a.pdf"), _result(run, "b.pdf")], T)

        assert (table.table, table.file, table.total_row_count) == ("", None, 0)
        store.put_table.assert_not_awaited()
        store.rows.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_a_result_delivered_twice_adds_its_rows_once(self, store: _Store):
        run = _run(file_count=1)
        result = _result(run, "a.pdf", [{"item": "Rack", "amount": 1}], store)

        table = await ExtractionTable.assemble(run, [result, result], T)

        assert (table.file_count, table.total_row_count) == (1, 1)

    @pytest.mark.asyncio
    async def test_cells_cannot_break_the_preview(self, store: _Store):
        run = _run(file_count=1)

        table = await ExtractionTable.assemble(
            run, [_result(run, "a.pdf", [{"item": "a|b\nc", "amount": None}], store)], T
        )

        assert "| a.pdf | a.pdf | a\\|b c |  |" in table.table
        assert store.tables[0][3][0][2:] == ["a|b\nc", None]

    @pytest.mark.asyncio
    async def test_a_table_spanning_collections_names_each_rows_collection(self, store: _Store):
        run = _run(file_count=1, show_collection=True)

        table = await ExtractionTable.assemble(run, [_result(run, "a.pdf", [{"item": "x", "amount": 1}], store)], T)

        assert table.columns[0] == "Collection"
        assert "| finance-db/invoices | a.pdf |" in table.table
        assert store.tables[0][2][0] == "Collection"
        assert store.tables[0][3][0][0] == "finance-db/invoices"

    @pytest.mark.asyncio
    async def test_unsure_rows_are_kept_and_marked_in_the_preview_and_the_file(self, store: _Store):
        run = _run(file_count=1)
        rows = [
            {"item": "Laptop", "amount": 1450.0, RecordSchema.MATCH_FIELD: "yes"},
            {"item": "Docking station", "amount": 220.0, RecordSchema.MATCH_FIELD: "unsure"},
        ]

        table = await ExtractionTable.assemble(run, [_result(run, "a.pdf", rows, store)], T)

        assert table.columns[-1] == "Match"
        assert "| Docking station | 220.0 | unsure, please check |" in table.table
        assert "**Unsure:** 1 rows may not meet the condition" in table.summary
        assert [row[-1] for row in store.tables[0][3]] == ["yes", "unsure, please check"]

    @pytest.mark.asyncio
    async def test_without_unsure_rows_there_is_no_match_column(self, store: _Store):
        run = _run(file_count=1)
        rows = [{"item": "Laptop", "amount": 1450.0, RecordSchema.MATCH_FIELD: "yes"}]

        table = await ExtractionTable.assemble(run, [_result(run, "a.pdf", rows, store)], T)

        assert "Match" not in table.columns
        assert "yes" not in table.table
        assert store.tables[0][2] == ["Path", "File", "Item", "Amount"]

    @pytest.mark.asyncio
    async def test_the_marked_table_condenses_for_later_turns(self, store: _Store):
        run = _run(file_count=1)
        table = await ExtractionTable.assemble(run, [_result(run, "a.pdf", [{"item": "x", "amount": 1}], store)], T)

        assert ExtractedTableMarkup.condensed(table.table) == "[A table of 1 extracted rows was shown here.]"


def _request(path: str = "invoices/2025/a.pdf") -> DocumentExtractionRequestedEvent:
    return DocumentExtractionRequestedEvent(run=_run(file_count=1), document=_summary(path), record_schema=SCHEMA)


def _displayer() -> MagicMock:
    displayer = MagicMock(spec=EventDisplayer)
    displayer.display_thought = AsyncMock()
    return displayer


def _thoughts(displayer: MagicMock) -> list[str]:
    return [call.args[0] for call in displayer.display_thought.await_args_list]


class _Thread:
    """The conversation's (or run's) context, in memory."""

    def __init__(self) -> None:
        self.values: dict[str, Any] = {}

    async def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    async def set(self, key: str, value: Any) -> None:
        self.values[key] = value

    async def delete(self, key: str) -> None:
        self.values.pop(key, None)

    async def pop(self, key: str, default: Any = None) -> Any:
        return self.values.pop(key, default)

    async def set_if_absent(self, key: str, value: Any) -> bool:
        if key in self.values:
            return False
        self.values[key] = value
        return True


def _redis(done: int = 1) -> MagicMock:
    redis = MagicMock()
    redis.incr = AsyncMock(return_value=done)
    redis.expire = AsyncMock()
    return redis


def _loaded(text: str) -> KnowledgeDocument:
    return KnowledgeDocument(
        summary=_summary("invoices/2025/a.pdf"), text=text, text_length=len(text), start=0, end=len(text)
    )


def _llm_config() -> MagicMock:
    llm_config = MagicMock()
    llm_config.cost_reporting_llm.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
    llm_config.cost_reporting_llm.return_value.__aexit__ = AsyncMock(return_value=None)
    return llm_config


async def _extract_document(
    extracted: DocumentExtractionResult | AsyncMock,
    text: str = "text",
    config: TableConfig | None = None,
    displayer: MagicMock | None = None,
    request: DocumentExtractionRequestedEvent | None = None,
    done: int = 1,
) -> DocumentExtractedEvent:
    extract = extracted if isinstance(extracted, AsyncMock) else AsyncMock(return_value=extracted)
    with (
        patch(f"{EXTRACTION}.KnowledgeDocumentReader.load_document", AsyncMock(return_value=_loaded(text))),
        patch(f"{EXTRACTION}.RecordExtractor.extract", extract),
        patch.object(TableConfig, "extraction_llm", return_value=_llm_config()),
    ):
        return await DocumentRecordExtraction.extract(
            request or _request(), config or _config(), displayer or _displayer(), T, _redis(done), None
        )


def _provenance() -> RecordProvenance:
    return RecordProvenance.from_summary(_summary("invoices/2025/a.pdf"))


class TestDocumentExtraction:
    @pytest.mark.asyncio
    async def test_the_rows_are_stored_whole_and_the_event_carries_their_key_and_counts(self, store: _Store):
        rows = [
            {"item": "y" * 2000, "amount": 1.5, RecordSchema.MATCH_FIELD: "yes"},
            {"item": "Dock", "amount": 2.0, RecordSchema.MATCH_FIELD: "unsure"},
        ]
        request = _request()

        result = await _extract_document(DocumentExtractionResult.succeeded(_provenance(), rows, 1), request=request)

        store.put_rows.assert_awaited_once_with("x1", request.event_id, rows)
        assert result.rows_key == f"record-extraction/x1/rows/{request.event_id}.json"
        assert (result.row_count, result.unsure_count, result.failure_reason, result.partly_read) == (2, 1, None, False)
        assert store.stored_rows[result.rows_key][0]["item"] == "y" * 2000
        assert "rows" not in DocumentExtractedEvent.model_fields

    @pytest.mark.asyncio
    async def test_the_progress_shows_the_first_rows_a_document_yielded(self, store: _Store):
        rows = [{"item": "Rack", "amount": 1200}, {"item": "Cable", "amount": 20}, {"item": "Fan", "amount": 5}]
        displayer = _displayer()

        await _extract_document(DocumentExtractionResult.succeeded(_provenance(), rows, 1), displayer=displayer)

        assert _thoughts(displayer) == ["1 of 1 · invoices/2025/a.pdf: 3 rows — Rack, 1200; Cable, 20 …"]

    @pytest.mark.asyncio
    async def test_a_document_without_rows_stores_nothing(self, store: _Store):
        displayer = _displayer()

        result = await _extract_document(DocumentExtractionResult.succeeded(_provenance(), [], 1), displayer=displayer)

        store.put_rows.assert_not_awaited()
        assert (result.rows_key, result.row_count, result.failure_reason) == (None, 0, None)
        assert _thoughts(displayer) == ["1 of 1 · invoices/2025/a.pdf: 0 rows"]

    @pytest.mark.asyncio
    async def test_the_count_of_finished_documents_never_passes_the_total(self, store: _Store):
        displayer = _displayer()

        await _extract_document(DocumentExtractionResult.succeeded(_provenance(), [], 1), displayer=displayer, done=3)

        assert _thoughts(displayer)[0].startswith("1 of 1 ·")

    @pytest.mark.asyncio
    async def test_any_error_becomes_the_documents_failure(self, store: _Store):
        displayer = _displayer()
        with patch(f"{EXTRACTION}.KnowledgeDocumentReader.load_document", AsyncMock(side_effect=RuntimeError("down"))):
            result = await DocumentRecordExtraction.extract(_request(), _config(), displayer, T, _redis(), None)

        assert result.failure_reason == "RuntimeError: down"
        assert (result.rows_key, result.row_count) == (None, 0)
        store.put_rows.assert_not_awaited()
        assert _thoughts(displayer) == ["1 of 1 · invoices/2025/a.pdf: failed, RuntimeError: down"]

    @pytest.mark.asyncio
    async def test_a_failure_to_store_the_rows_is_the_documents_failure(self, store: _Store):
        store.put_rows.side_effect = OSError("bucket gone")

        result = await _extract_document(
            DocumentExtractionResult.succeeded(_provenance(), [{"item": "Rack", "amount": 1}], 1)
        )

        assert result.failure_reason == "OSError: bucket gone"

    @pytest.mark.asyncio
    async def test_a_model_that_could_not_extract_fails_the_document_with_its_reason(self, store: _Store):
        failed = DocumentExtractionResult.failed_with(_provenance(), "x" * 500, 3)

        result = await _extract_document(failed)

        assert result.failure_reason == "x" * 300
        store.put_rows.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_a_long_document_is_read_in_part_and_its_rows_say_so(self, store: _Store):
        extracted = DocumentExtractionResult.succeeded(
            _provenance(), [{"item": "Rack", "amount": 1.0}], 31, partial=True
        )
        extract = AsyncMock(return_value=extracted)
        displayer = _displayer()

        result = await _extract_document(
            extract, text="x" * 2000, config=_config(max_document_chars=1000), displayer=displayer
        )
        run = _run(file_count=1)
        table = await ExtractionTable.assemble(run, [result.model_copy(update={"run": run})], T)

        assert result.failure_reason is None
        assert result.partly_read
        assert extract.await_args.kwargs["max_windows"] == 12
        assert "a.pdf (partly read)" in table.table
        assert "**Partly read (rows may be missing):** invoices/2025/a.pdf" in table.summary
        assert "is long: reading only its relevant parts" in _thoughts(displayer)[0]

    @pytest.mark.asyncio
    async def test_a_long_document_read_whole_is_announced_when_it_starts(self, store: _Store):
        extract = AsyncMock(return_value=DocumentExtractionResult.succeeded(_provenance(), [], 4))
        displayer = _displayer()

        await _extract_document(extract, text="x" * 40_001, displayer=displayer)

        assert _thoughts(displayer)[0] == "Reading invoices/2025/a.pdf, a long document."
        assert extract.await_args.kwargs["max_windows"] is None

    @pytest.mark.asyncio
    async def test_a_short_document_is_not_announced(self, store: _Store):
        displayer = _displayer()

        await _extract_document(DocumentExtractionResult.succeeded(_provenance(), [], 1), displayer=displayer)

        assert len(_thoughts(displayer)) == 1

    @pytest.mark.asyncio
    async def test_a_document_still_being_read_says_so_at_intervals(self, store: _Store):
        async def slow(*args: Any, **kwargs: Any) -> DocumentExtractionResult:
            await asyncio.sleep(0.2)
            return DocumentExtractionResult.succeeded(_provenance(), [], 1)

        displayer = _displayer()
        quick = functools.partial(ReadingHeartbeat.around, interval_seconds=0.05)
        with patch.object(ReadingHeartbeat, "around", quick):
            await _extract_document(AsyncMock(side_effect=slow), displayer=displayer)

        still = [thought for thought in _thoughts(displayer) if thought.startswith("Still reading")]
        assert len(still) >= 2
        assert still[0] == "Still reading invoices/2025/a.pdf (1 min)."
        assert _thoughts(displayer)[-1] == "1 of 1 · invoices/2025/a.pdf: 0 rows"


class TestHeartbeat:
    @pytest.mark.asyncio
    async def test_the_heartbeat_counts_minutes_and_stops_with_its_body(self):
        said: list[int] = []

        async def say(minutes: int) -> None:
            said.append(minutes)

        async with ReadingHeartbeat.around(say, interval_seconds=0.02):
            await asyncio.sleep(0.11)
        count = len(said)
        await asyncio.sleep(0.06)

        assert count >= 3
        assert len(said) == count
        assert set(said) == {1}

    @pytest.mark.asyncio
    async def test_a_sign_of_life_that_cannot_be_shown_never_fails_the_reading(self):
        say = AsyncMock(side_effect=ConnectionError("NATS gone"))

        async with ReadingHeartbeat.around(say, interval_seconds=0.02):
            await asyncio.sleep(0.07)

        assert say.await_count >= 2

    @pytest.mark.asyncio
    async def test_a_body_shorter_than_the_interval_says_nothing(self):
        say = AsyncMock()

        async with ReadingHeartbeat.around(say, interval_seconds=1.0):
            await asyncio.sleep(0)

        say.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_a_body_that_raises_stops_the_heartbeat(self):
        say = AsyncMock()

        async def read() -> None:
            async with ReadingHeartbeat.around(say, interval_seconds=0.01):
                raise RuntimeError("model down")

        with pytest.raises(RuntimeError):
            await read()
        await asyncio.sleep(0.05)

        say.assert_not_awaited()


def _extract_request(**fields: Any) -> ExtractRecordsEvent:
    return ExtractRecordsEvent(selection=_selection(), fields="item, amount", collections=[FINANCE, LEGAL], **fields)


def _schema_llm() -> Any:
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=MagicMock())
    context.__aexit__ = AsyncMock(return_value=None)
    return context


class TestPlanning:
    @pytest.mark.asyncio
    async def test_every_selected_document_is_requested_at_once(self):
        documents = [_summary("invoices/2025/a.pdf"), _summary("invoices/2025/b.pdf", LEGAL)]
        resolve = AsyncMock(return_value=KnowledgeDocumentSelectionResult(documents=documents))
        displayer = _displayer()
        with (
            patch(f"{PLANNER}.KnowledgeDocumentSelector.resolve", resolve),
            patch(f"{PLANNER}.RecordSchemaBuilder.build", AsyncMock(return_value=SCHEMA)),
            patch.object(LLMConfig, "get_model_info", return_value={}),
            patch.object(LLMConfig, "cost_reporting_llm", return_value=_schema_llm()),
        ):
            planned = await ExtractionPlanner.plan(
                _extract_request(instructions="only hardware", row_terms="Rack"),
                _config(),
                displayer,
                T,
                _Thread(),
                None,
            )

        assert resolve.await_args.args[2:4] == (1000, "invoices/**")
        assert [request.document.path for request in planned] == ["invoices/2025/a.pdf", "invoices/2025/b.pdf"]
        assert (planned[0].instructions, planned[0].row_terms, planned[0].record_schema) == (
            "only hardware",
            "Rack",
            SCHEMA,
        )
        run = planned[0].run
        assert (run.file_count, run.field_names, run.show_collection, run.cut_short, run.sample) == (
            2,
            ["item", "amount"],
            True,
            False,
            False,
        )
        assert run.collections == [FINANCE, LEGAL]
        displayer.display_thought.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_no_matching_document_answers_without_extracting(self):
        resolve = AsyncMock(return_value=KnowledgeDocumentSelectionResult(documents=[]))
        build = AsyncMock()
        with (
            patch(f"{PLANNER}.KnowledgeDocumentSelector.resolve", resolve),
            patch(f"{PLANNER}.RecordSchemaBuilder.build", build),
        ):
            answer = await ExtractionPlanner.plan(
                _extract_request(tool_call_id="c1", notices=["note"]), _config(), _displayer(), T, _Thread(), None
            )

        assert isinstance(answer, RecordsExtractedEvent)
        assert answer.tool_call_id == "c1"
        assert answer.summary == "No document matches the selection, so nothing was extracted.\n\nnote"
        build.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_a_problem_the_user_can_act_on_answers_instead_of_failing_the_run(self):
        resolve = AsyncMock(side_effect=ValueError("glob is empty"))
        with patch(f"{PLANNER}.KnowledgeDocumentSelector.resolve", resolve):
            answer = await ExtractionPlanner.plan(_extract_request(), _config(), _displayer(), T, _Thread(), None)

        assert answer.summary.startswith("The table could not be extracted: glob is empty")

    @pytest.mark.asyncio
    async def test_a_schema_the_model_could_not_design_answers_instead_of_failing_the_run(self):
        documents = [_summary("invoices/2025/a.pdf")]
        with (
            patch(
                f"{PLANNER}.KnowledgeDocumentSelector.resolve",
                AsyncMock(return_value=KnowledgeDocumentSelectionResult(documents=documents)),
            ),
            patch(f"{PLANNER}.RecordSchemaBuilder.build", AsyncMock(side_effect=ValueError("no columns"))),
            patch.object(LLMConfig, "get_model_info", return_value={}),
            patch.object(LLMConfig, "cost_reporting_llm", return_value=_schema_llm()),
        ):
            answer = await ExtractionPlanner.plan(_extract_request(), _config(), _displayer(), T, _Thread(), None)

        assert answer.summary.startswith("The table could not be extracted: no columns")

    def test_a_stored_profile_with_the_removed_limits_still_validates(self):
        config = RecordExtractionConfig.model_validate(
            {"max_files": 5, "minutes_per_turn": 3, "max_rows": 20, "max_documents_total": 300}
        )

        assert config.max_documents_total == 300
        assert not {"max_files", "minutes_per_turn", "max_rows"} & set(config.model_dump())


def _decided(*call_ids: str) -> ToolCallsDecidedEvent:
    state = ToolLoopState(messages=[], mode=ToolLoopMode.ANSWER)
    return ToolCallsDecidedEvent(state=state, tool_call_ids=list(call_ids))


def _scope() -> KnowledgeDocumentRunScope:
    return KnowledgeDocumentRunScope(
        collections=[KnowledgeDocumentCollection(identifier="finance/invoices", collection=FINANCE, label="F")]
    )


async def _tool_call(arguments: dict[str, Any], run_context: _Thread, call_id: str = "c1") -> Any:
    call = ToolCallApprovedEvent(tool_call_id=call_id, name="extract_records", arguments=arguments, kind="capability")
    with patch(SCOPE_OF, return_value=_scope()):
        return await RecordExtraction.extract_tool_call_step(
            MagicMock(), call=call, request=RunToolLoopEvent(), tool=_config(), t=T, run_context=run_context
        )


class TestAsATool:
    @pytest.mark.asyncio
    async def test_a_chosen_extraction_runs_over_the_collections_of_the_run(self):
        request = await _tool_call(
            {
                "any_of": [{"path_glob": "invoices/**"}],
                "fields": "item, amount",
                "instructions": "hardware",
                "row_terms": "Laptop|Rack",
                "document_terms": "Hooli",
            },
            _Thread(),
        )

        assert isinstance(request, ExtractRecordsEvent)
        assert (request.tool_call_id, request.collections, request.instructions) == ("c1", [FINANCE], "hardware")
        assert (request.row_terms, request.document_terms, request.confirmed) == ("Laptop|Rack", "Hooli", False)

    @pytest.mark.asyncio
    async def test_invalid_arguments_go_back_to_the_model(self):
        result = await _tool_call({"fields": ""}, _Thread())

        assert result.is_error
        assert "Invalid arguments" in result.content

    @pytest.mark.asyncio
    async def test_a_new_extraction_without_documents_goes_back_to_the_model(self):
        result = await _tool_call({"fields": "item, amount"}, _Thread())

        assert result.is_error
        assert "needs any_of and fields" in result.content

    @pytest.mark.parametrize("flag", [True, "true"])
    @pytest.mark.asyncio
    async def test_confirming_a_sample_needs_no_selection_and_runs_over_the_runs_collections(self, flag: Any):
        request = await _tool_call({"confirm_sample": flag}, _Thread())

        assert isinstance(request, ExtractRecordsEvent)
        assert (request.confirmed, request.selection, request.collections) == (True, None, [FINANCE])
        assert request.tool_call_id == "c1"

    def test_continuing_is_no_longer_an_argument(self):
        from swiss_ai_hub.agent.capabilities.record_extraction.extract_records_tool_arguments import (
            ExtractRecordsToolArguments,
        )

        properties = ExtractRecordsToolArguments.model_json_schema()["properties"]
        assert "confirm_sample" in properties
        assert "document_terms" in properties
        assert "continue_pending" not in properties

    @pytest.mark.asyncio
    async def test_one_answer_confirms_once_and_a_redelivered_call_still_runs(self):
        run_context = _Thread()

        first = await _tool_call({"confirm_sample": True}, run_context, "c1")
        redelivered = await _tool_call({"confirm_sample": True}, run_context, "c1")
        second = await _tool_call({"confirm_sample": True}, run_context, "c2")

        assert isinstance(first, ExtractRecordsEvent)
        assert isinstance(redelivered, ExtractRecordsEvent)
        assert isinstance(second, ToolResultEvent)
        assert "the rest waits for the user" in second.content

    @pytest.mark.asyncio
    async def test_a_sample_uses_up_the_answer_so_confirming_waits_for_the_user(self):
        run_context = _Thread()
        sample = RecordsExtractedEvent(
            extraction_id="x", summary="s", table="| a |", row_count=1, tool_call_id="c1", awaiting_confirmation=True
        )
        result = await RecordExtraction.extract_tool_result_step(
            MagicMock(), extracted=sample, decided=_decided("c1"), run_context=run_context
        )

        refused = await _tool_call({"confirm_sample": True}, run_context, "c2")

        assert "only a sample of the selection" in result.content
        assert "confirm_sample set to true" in result.content
        assert isinstance(refused, ToolResultEvent)
        assert "the rest waits for the user" in refused.content

    @pytest.mark.asyncio
    async def test_a_sample_does_not_stop_a_new_extraction_in_the_same_answer(self):
        run_context = _Thread()
        sample = RecordsExtractedEvent(extraction_id="x", summary="s", tool_call_id="c1", awaiting_confirmation=True)
        await RecordExtraction.extract_tool_result_step(
            MagicMock(), extracted=sample, decided=_decided("c1"), run_context=run_context
        )

        request = await _tool_call({"any_of": [{"path_glob": "invoices/2025/**"}], "fields": "item"}, run_context, "c2")

        assert isinstance(request, ExtractRecordsEvent)

    @pytest.mark.asyncio
    async def test_a_complete_extraction_leaves_confirming_open(self):
        run_context = _Thread()
        whole = RecordsExtractedEvent(extraction_id="x", summary="s", table="| a |", row_count=1, tool_call_id="c1")

        result = await RecordExtraction.extract_tool_result_step(
            MagicMock(), extracted=whole, decided=_decided("c1"), run_context=run_context
        )

        assert run_context.values == {}
        assert "only a sample" not in result.content

    @pytest.mark.asyncio
    async def test_the_model_reads_the_summary_and_is_told_not_to_retype_the_table(self, store: _Store):
        run = _run(file_count=1, tool_call_id="c1")
        table = await ExtractionTable.assemble(run, [_result(run, "a.pdf", [{"item": "x", "amount": 1}], store)], T)

        assert await answers_an_extraction_call(table, _decided("c1"))
        result = await RecordExtraction.extract_tool_result_step(
            MagicMock(), extracted=table, decided=_decided("c1"), run_context=_Thread()
        )

        assert result.tool_call_id == "c1"
        assert "Do not write a table" in result.content
        assert "the first 1 of its 1 rows, and can download all of them as table-x1.csv" in result.content
        assert "| a.pdf | a.pdf | x | 1 |" in result.content

    @pytest.mark.asyncio
    async def test_an_answer_without_a_table_hands_back_only_the_summary(self):
        answer = RecordsExtractedEvent(extraction_id="x", summary="No document matches.", tool_call_id="c1")

        assert not await answers_an_extraction_call(answer, _decided("c2"))
        result = await RecordExtraction.extract_tool_result_step(
            MagicMock(), extracted=answer, decided=_decided("c1"), run_context=_Thread()
        )

        assert result.content == "No document matches."

    def test_a_long_table_reaches_the_model_only_in_part(self):
        rows = "\n".join(f"| row {index} | {'x' * 80} |" for index in range(500))
        extracted = RecordsExtractedEvent(extraction_id="x", summary="s", table=rows, row_count=500, tool_call_id="c")

        assert len(RecordsToolResult.content(extracted)) < 2_500


class TableAgent(Agent):
    tools = ToolLoop.over(KnowledgeDocumentTools, RecordSelectionTools, RecordExtraction)

    @step()
    async def open_step(self, event: UserMessageEvent) -> Conversation.ContextualizeRequest:
        return Conversation.contextualize(history=event.messages, message=event)

    @step()
    async def loop_step(self, ctx: Conversation.Contextualized) -> ToolLoop.RunRequest:
        return TableAgent.tools.run(ctx.history)

    @step()
    async def extract_step(self, finished: ToolLoop.Finished) -> RecordExtraction.ExtractRequest:
        return RecordExtraction.extract(_selection(), "item", [FINANCE])

    @step()
    async def answer_step(self, extracted: RecordExtraction.Extracted) -> Conversation.CompleteRequest:
        return Conversation.complete(answer=LLMEvent(), stop=StopEvent())


class TableAgentConfig(RecordExtractionFields, ToolLoopFields, AgentConfig):
    pass


def test_a_blueprint_calling_and_offering_the_extraction_validates():
    TableAgent.validate_workflow(TableAgentConfig)

    installed = {capability.__name__ for capability in TableAgent.installed_capabilities()}
    assert {"RecordExtraction", "ToolLoop", "Conversation"} <= installed
    assert {"plan_extraction_step", "extract_document_step", "assemble_table_step", "extract_tool_call_step"} <= {
        step.__name__ for step in TableAgent.get_steps()
    }


def test_a_config_without_the_extraction_settings_is_refused():
    class LoopOnlyConfig(ToolLoopFields, AgentConfig):
        pass

    with pytest.raises(ValueError, match="RecordExtractionFields"):
        TableAgent.validate_workflow(LoopOnlyConfig)
