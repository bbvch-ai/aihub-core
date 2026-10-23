"""A selection larger than one answer is never cut: the answer shows a sample and offers to narrow the request or to
continue part by part; rows beyond what one answer shows come first on the next; above the profile's ceiling only
narrowing is offered."""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import ExtractRecordsEvent, RecordsExtractedEvent
from swiss_ai_hub.core.generative_ai import (
    BucketNamespacePair,
    KnowledgeDocumentCriteria,
    KnowledgeDocumentSelection,
    KnowledgeDocumentSelectionResult,
    KnowledgeDocumentSummary,
    LLMConfig,
    RecordField,
    RecordSchema,
)
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_config import KnowledgeDocumentConfig
from swiss_ai_hub.agent.capabilities.record_extraction.document_extracted_event import DocumentExtractedEvent
from swiss_ai_hub.agent.capabilities.record_extraction.document_extraction_requested_event import (
    DocumentExtractionRequestedEvent,
)
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_estimate import ExtractionEstimate
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_planner import ExtractionPlanner
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_progress import ExtractionProgress
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_table import (
    INLINE_CHARACTERS,
    INLINE_ROWS,
    ExtractionTable,
)
from swiss_ai_hub.agent.capabilities.record_extraction.pending_extraction import PendingExtraction
from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction import RecordExtraction
from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction_config import RecordExtractionConfig
from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction_fields import RecordExtractionFields
from swiss_ai_hub.agent.capabilities.record_extraction.selection_facets import SelectionFacets
from swiss_ai_hub.agent.i18n.agent_locale_handler import AgentLocaleHandler

T = AgentLocaleHandler("en")
FINANCE = BucketNamespacePair(bucket_name="finance-db", namespace_name="invoices")
PLANNER = "swiss_ai_hub.agent.capabilities.record_extraction.extraction_planner"
SCHEMA = RecordSchema(
    fields=[
        RecordField(name="item", type="string", description="The billed item."),
        RecordField(name="amount", type="number", description="The amount in CHF."),
    ]
)


class PartsConfig(RecordExtractionFields, AgentConfig):
    pass


class _Thread:
    """The conversation's thread context, in memory."""

    def __init__(self) -> None:
        self.values: dict[str, Any] = {}

    async def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    async def set(self, key: str, value: Any) -> None:
        self.values[key] = value

    async def delete(self, key: str) -> None:
        self.values.pop(key, None)


def _config(**settings: Any) -> PartsConfig:
    return PartsConfig(
        agent_id="tables",
        name=LocaleString(en="Tables"),
        description=LocaleString(en="Tables fixture"),
        llm=LLMConfig(model_name="text-generation/main"),
        knowledge_documents=KnowledgeDocumentConfig(enabled=True, path_glob="invoices/**"),
        record_extraction=RecordExtractionConfig(**settings),
    )


def _document(path: str, pages: int = 1) -> KnowledgeDocumentSummary:
    return KnowledgeDocumentSummary(
        id=path.replace("/", "-"),
        collection=FINANCE,
        path=path,
        filename=path.rsplit("/", 1)[-1],
        title=path,
        file_type="pdf",
        number_of_pages=pages,
        updated_at=datetime(2025, 1, 1, tzinfo=UTC),
    )


def _documents(count: int) -> list[KnowledgeDocumentSummary]:
    return [_document(f"invoices/{2024 + index % 2}/q{index % 4 + 1}/inv-{index:03d}.pdf") for index in range(count)]


def _request(**fields: Any) -> ExtractRecordsEvent:
    selection = KnowledgeDocumentSelection(any_of=[KnowledgeDocumentCriteria(content_query="ACME AG")])
    return ExtractRecordsEvent(selection=selection, fields="item, amount", collections=[FINANCE], **fields)


def _displayer() -> MagicMock:
    displayer = MagicMock(spec=EventDisplayer)
    displayer.display_thought = AsyncMock()
    return displayer


def _schema_llm() -> Any:
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=MagicMock())
    context.__aexit__ = AsyncMock(return_value=None)
    return context


async def _plan(request: ExtractRecordsEvent, config: PartsConfig, selected: KnowledgeDocumentSelectionResult, thread):
    with (
        patch(f"{PLANNER}.KnowledgeDocumentSelector.resolve", AsyncMock(return_value=selected)),
        patch(f"{PLANNER}.RecordSchemaBuilder.build", AsyncMock(return_value=SCHEMA)),
        patch.object(LLMConfig, "get_model_info", return_value={}),
        patch.object(LLMConfig, "cost_reporting_llm", return_value=_schema_llm()),
    ):
        return await ExtractionPlanner.plan(request, config, _displayer(), T, thread, None)


def _rows(request_event: Any, count: int) -> DocumentExtractedEvent:
    rows = [{"item": f"item {index}", "amount": index} for index in range(count)]
    return DocumentExtractedEvent(
        run=request_event.run, request_event_id=request_event.event_id, document=request_event.document, rows=rows
    )


class TestEstimate:
    def test_parts_fit_the_minutes_and_the_files_per_answer(self):
        documents = [_document(f"invoices/{index}.pdf", pages=5) for index in range(30)]

        parts = ExtractionEstimate.batches(documents, max_files=100, minutes_per_turn=1, parallel=2)

        assert [len(part) for part in parts] == [12, 12, 6]
        assert ExtractionEstimate.batches(documents, max_files=10, minutes_per_turn=30, parallel=4)[0] == documents[:10]

    def test_a_spreadsheet_counts_as_more_than_its_one_page(self):
        sheet = _document("invoices/list.xlsx").model_copy(update={"file_type": "xlsx"})

        assert ExtractionEstimate.windows(sheet) > ExtractionEstimate.windows(_document("invoices/a.pdf"))


class TestTooBroad:
    @pytest.mark.asyncio
    async def test_a_selection_too_large_for_one_answer_extracts_a_sample_and_waits(self):
        thread = _Thread()
        documents = _documents(12)

        planned = await _plan(
            _request(), _config(max_files=4), KnowledgeDocumentSelectionResult(documents=documents), thread
        )

        assert len(planned) == 3
        run = planned[0].run
        assert (run.sample, run.total_documents, run.parts) == (True, 12, 3)
        assert any("12 documents match" in notice for notice in run.notices)
        assert any("By folder:" in notice for notice in run.notices)
        assert any("in 3 parts" in notice for notice in run.notices)
        pending = await PendingExtraction.load(thread)
        assert (pending.part_starts, pending.next_part, pending.remaining_documents) == ([0, 4, 8], 0, 12)

    @pytest.mark.asyncio
    async def test_above_the_ceiling_only_narrowing_is_offered(self):
        thread = _Thread()

        planned = await _plan(
            _request(),
            _config(max_files=4),
            KnowledgeDocumentSelectionResult(documents=_documents(12), truncated=True),
            thread,
        )

        run = planned[0].run
        assert run.sample
        assert any("More than 12 documents match" in notice for notice in run.notices)
        assert any("Please narrow the request" in notice for notice in run.notices)
        assert "**By year in the path:** 2024, 2025" in run.notices
        assert any("of the first 12 documents by path" in notice for notice in run.notices)
        assert await PendingExtraction.load(thread) is None
        table, overflow = ExtractionTable.assemble(run, [_rows(request, 1) for request in planned], 500, T)
        assert table.summary.startswith("**Sample:** 3 of more than 12 matching documents")

    @pytest.mark.asyncio
    async def test_the_sample_answer_says_how_many_documents_are_left(self):
        thread = _Thread()
        planned = await _plan(
            _request(), _config(max_files=4), KnowledgeDocumentSelectionResult(documents=_documents(12)), thread
        )
        results = [_rows(request, 1) for request in planned]

        table, overflow = ExtractionTable.assemble(planned[0].run, results, 500, T)
        answer = await ExtractionProgress.record(planned[0].run, table, overflow, _config(), thread, T)

        assert answer.summary.startswith("**Sample:** 3 of 12 matching documents")
        assert answer.remaining_documents == 12

    def test_the_sample_spreads_over_the_largest_folders(self):
        documents = _documents(12)

        sample = SelectionFacets.sample(documents, 3)

        assert len({document.path.rsplit("/", 1)[0] for document in sample}) == 3


class TestContinuing:
    @pytest.mark.asyncio
    async def test_continuing_extracts_the_next_part_with_the_same_columns_once(self):
        thread = _Thread()
        await _plan(
            _request(), _config(max_files=4), KnowledgeDocumentSelectionResult(documents=_documents(12)), thread
        )

        planned = await ExtractionPlanner.plan(
            RecordExtraction.continue_pending([FINANCE]), _config(max_files=4), _displayer(), T, thread, None
        )

        assert [request.document.path for request in planned] == [doc.path for doc in _documents(12)[:4]]
        assert planned[0].record_schema == SCHEMA
        assert (planned[0].run.part, planned[0].run.parts, planned[0].run.first_document) == (1, 3, 1)
        assert (await PendingExtraction.load(thread)).next_part == 1

    @pytest.mark.asyncio
    async def test_a_part_reports_its_range_and_the_last_part_gives_the_totals(self):
        thread = _Thread()
        config = _config(max_files=6)
        await _plan(_request(), config, KnowledgeDocumentSelectionResult(documents=_documents(12)), thread)
        answers = []
        for _ in range(2):
            planned = await ExtractionPlanner.plan(
                RecordExtraction.continue_pending([FINANCE]), config, _displayer(), T, thread, None
            )
            table, overflow = ExtractionTable.assemble(planned[0].run, [_rows(r, 1) for r in planned], 500, T)
            answers.append(await ExtractionProgress.record(planned[0].run, table, overflow, config, thread, T))

        assert "**Part 1 of 2:** documents 1–6 of 12." in answers[0].summary
        assert "Reply *continue* for the next 6 documents" in answers[0].summary
        assert answers[0].remaining_documents == 6
        assert "**All 12 documents are extracted** in 2 parts: 12 rows found" in answers[1].summary
        assert answers[1].remaining_documents == 0
        assert await PendingExtraction.load(thread) is None

    @pytest.mark.asyncio
    async def test_rows_beyond_one_answer_come_first_when_continuing(self):
        thread = _Thread()
        config = _config(max_rows=3)
        planned = await _plan(_request(), config, KnowledgeDocumentSelectionResult(documents=_documents(2)), thread)
        table, overflow = ExtractionTable.assemble(planned[0].run, [_rows(r, 4) for r in planned], 3, T)
        first = await ExtractionProgress.record(planned[0].run, table, overflow, config, thread, T)

        more = await ExtractionPlanner.plan(
            RecordExtraction.continue_pending([FINANCE]), config, _displayer(), T, thread, None
        )

        assert (first.row_count, first.remaining_rows) == (3, 5)
        assert "5 more rows follow" in first.summary
        assert isinstance(more, RecordsExtractedEvent)
        assert (more.row_count, more.remaining_rows) == (3, 2)

    @pytest.mark.asyncio
    async def test_nothing_to_continue_says_so(self):
        answer = await ExtractionPlanner.plan(
            RecordExtraction.continue_pending([FINANCE]), _config(), _displayer(), T, _Thread(), None
        )

        assert answer.summary == "There is no table extraction to continue in this conversation."

    @pytest.mark.asyncio
    async def test_a_new_selection_replaces_the_unfinished_extraction(self):
        thread = _Thread()
        config = _config(max_files=4)
        await _plan(_request(), config, KnowledgeDocumentSelectionResult(documents=_documents(12)), thread)

        await _plan(_request(), config, KnowledgeDocumentSelectionResult(documents=_documents(2)), thread)

        assert await PendingExtraction.load(thread) is None

    @pytest.mark.asyncio
    async def test_a_conversation_that_lost_a_collection_ends_the_extraction(self):
        thread = _Thread()
        config = _config(max_files=4)
        await _plan(_request(), config, KnowledgeDocumentSelectionResult(documents=_documents(12)), thread)
        other = BucketNamespacePair(bucket_name="legal-db", namespace_name="contracts")

        answer = await ExtractionPlanner.plan(
            RecordExtraction.continue_pending([other]), config, _displayer(), T, thread, None
        )

        assert "no longer all available" in answer.summary
        assert await PendingExtraction.load(thread) is None

    @pytest.mark.asyncio
    async def test_rows_left_by_one_answer_are_not_shown_once_their_collection_is_out_of_reach(self):
        thread = _Thread()
        config = _config(max_rows=3)
        planned = await _plan(_request(), config, KnowledgeDocumentSelectionResult(documents=_documents(2)), thread)
        table, overflow = ExtractionTable.assemble(planned[0].run, [_rows(r, 4) for r in planned], 3, T)
        await ExtractionProgress.record(planned[0].run, table, overflow, config, thread, T)
        other = BucketNamespacePair(bucket_name="legal-db", namespace_name="contracts")

        answer = await ExtractionPlanner.plan(
            RecordExtraction.continue_pending([other]), config, _displayer(), T, thread, None
        )

        assert "no longer all available" in answer.summary
        assert (answer.row_count, answer.table) == (0, "")
        assert await PendingExtraction.load(thread) is None

    @pytest.mark.asyncio
    async def test_documents_outside_the_profiles_current_path_filter_are_left_out(self):
        thread = _Thread()
        await _plan(
            _request(), _config(max_files=4), KnowledgeDocumentSelectionResult(documents=_documents(12)), thread
        )
        narrowed = _config(max_files=4)
        narrowed.knowledge_documents.path_glob = "invoices/2024/**"

        planned = await ExtractionPlanner.plan(
            RecordExtraction.continue_pending([FINANCE]), narrowed, _displayer(), T, thread, None
        )

        assert all(request.document.path.startswith("invoices/2024/") for request in planned)
        assert any("no longer available" in notice for notice in planned[0].run.notices)


class TestInlinePages:
    def test_a_tool_calls_table_fits_what_a_chat_client_shows_inline_and_the_rest_waits(self):
        long_rows = [f"| invoices/{index}.pdf | {'clause ' * 150} |" for index in range(300)]

        _, inline_shown = ExtractionTable.page(["Path", "Clause"], long_rows, 500, inline=True)
        _, answer_shown = ExtractionTable.page(["Path", "Clause"], long_rows, 500)
        _, short_shown = ExtractionTable.page(
            ["Path", "Item"], [f"| a{index}.pdf | x |" for index in range(300)], 500, inline=True
        )

        assert sum(len(row) + 1 for row in long_rows[:inline_shown]) <= INLINE_CHARACTERS
        assert inline_shown < answer_shown
        assert short_shown == INLINE_ROWS

    @pytest.mark.asyncio
    async def test_rows_beyond_the_inline_page_of_a_tool_call_follow_on_continue(self):
        thread = _Thread()
        run = ExtractionPlanner._run(_request(tool_call_id="c1"), [_document("invoices/a.pdf")], SCHEMA)
        request = DocumentExtractionRequestedEvent(run=run, document=_document("invoices/a.pdf"), record_schema=SCHEMA)

        table, overflow = ExtractionTable.assemble(run, [_rows(request, 150)], 500, T)
        answer = await ExtractionProgress.record(run, table, overflow, _config(), thread, T)

        assert (answer.row_count, answer.remaining_rows) == (INLINE_ROWS, 50)


class TestPartsThatDidNotFinish:
    @pytest.mark.asyncio
    async def test_a_part_whose_run_died_is_extracted_again_and_the_totals_stay_true(self):
        thread = _Thread()
        config = _config(max_files=4)
        await _plan(_request(), config, KnowledgeDocumentSelectionResult(documents=_documents(8)), thread)

        lost = await ExtractionPlanner.plan(
            RecordExtraction.continue_pending([FINANCE]), config, _displayer(), T, thread, None
        )
        second = await ExtractionPlanner.plan(
            RecordExtraction.continue_pending([FINANCE]), config, _displayer(), T, thread, None
        )
        await _record(second, config, thread)
        retried = await ExtractionPlanner.plan(
            RecordExtraction.continue_pending([FINANCE]), config, _displayer(), T, thread, None
        )
        answer = await _record(retried, config, thread)

        assert (lost[0].run.part, second[0].run.part, retried[0].run.part) == (1, 2, 1)
        assert answer.remaining_documents == 0
        assert "All 8 documents are extracted" in answer.summary
        assert await PendingExtraction.load(thread) is None

    @pytest.mark.asyncio
    async def test_documents_never_extracted_are_not_counted_as_extracted(self):
        pending = PendingExtraction(
            extraction_id="x",
            documents=_documents(8),
            part_starts=[0, 4],
            next_part=2,
            finished_parts=[0, 1],
            extracted_files=4,
            rows_found=4,
        )

        assert ExtractionProgress._totals(pending, T).startswith("**4 of 8 documents are extracted**")


async def _record(planned: list, config: PartsConfig, thread: _Thread) -> RecordsExtractedEvent:
    results = [_rows(request, 1) for request in planned]
    table, overflow = ExtractionTable.assemble(planned[0].run, results, 500, T)
    return await ExtractionProgress.record(planned[0].run, table, overflow, config, thread, T)


class TestDocumentsWithoutRows:
    def test_documents_that_gave_no_rows_are_named_apart_from_failed_ones(self):
        documents = [_document("contracts/a.pdf"), _document("contracts/b.pdf"), _document("contracts/c.pdf")]
        run = ExtractionPlanner._run(_request(), documents, SCHEMA)
        results = [
            DocumentExtractedEvent(
                run=run, request_event_id="r1", document=documents[0], rows=[{"item": "x", "amount": 1}]
            ),
            DocumentExtractedEvent(run=run, request_event_id="r2", document=documents[1], rows=[]),
            DocumentExtractedEvent(run=run, request_event_id="r3", document=documents[2], failure_reason="unreadable"),
        ]

        table, _ = ExtractionTable.assemble(run, results, 10, T)

        assert "**No rows from:** contracts/b.pdf" in table.summary
        assert "contracts/c.pdf" not in table.summary.split("**No rows from:**")[1].split("\n")[0]


class TestUnsureRows:
    def test_unsure_rows_are_kept_and_marked_with_a_count(self):
        run = ExtractionPlanner._run(_request(), [_document("invoices/a.pdf")], SCHEMA)
        rows = [
            {"item": "Laptop", "amount": 1450.0, RecordSchema.MATCH_FIELD: "yes"},
            {"item": "Docking station", "amount": 220.0, RecordSchema.MATCH_FIELD: "unsure"},
        ]
        result = DocumentExtractedEvent(run=run, request_event_id="r1", document=_document("invoices/a.pdf"), rows=rows)

        table, _ = ExtractionTable.assemble(run, [result], 10, T)

        assert table.columns[-1] == "Match"
        assert "| Docking station | 220.0 | unsure, please check |" in table.table
        assert "**Unsure:** 1 rows may not meet the condition" in table.summary

    def test_without_unsure_rows_there_is_no_match_column(self):
        run = ExtractionPlanner._run(_request(), [_document("invoices/a.pdf")], SCHEMA)
        rows = [{"item": "Laptop", "amount": 1450.0, RecordSchema.MATCH_FIELD: "yes"}]
        result = DocumentExtractedEvent(run=run, request_event_id="r1", document=_document("invoices/a.pdf"), rows=rows)

        table, _ = ExtractionTable.assemble(run, [result], 10, T)

        assert "Match" not in table.columns
        assert "yes" not in table.table
