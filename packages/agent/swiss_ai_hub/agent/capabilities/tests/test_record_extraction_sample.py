"""One answer extracts the whole selection. Above `SAMPLE_ABOVE_DOCUMENTS` the user first sees a sample from the
documents likeliest to hold wanted rows and confirms; the confirmation extracts every document with the sample's
columns. Above the profile's ceiling only narrowing is offered."""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import ExtractRecordsEvent, RecordsExtractedEvent
from swiss_ai_hub.core.generative_ai import (
    BucketNamespacePair,
    ExtractionFileStore,
    InvalidSearchPatternError,
    KnowledgeContentSearchTimeoutError,
    KnowledgeDocumentCriteria,
    KnowledgeDocumentSelection,
    KnowledgeDocumentSelectionResult,
    KnowledgeDocumentSummary,
    KnowledgeSearchBudget,
    KnowledgeSemanticMatch,
    KnowledgeSemanticRanking,
    KnowledgeSemanticSearchUnavailableError,
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
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_sample import (
    SAMPLE_ABOVE_DOCUMENTS,
    SAMPLE_DOCUMENTS,
    ExtractionSample,
)
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_table import ExtractionTable
from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction import RecordExtraction
from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction_config import RecordExtractionConfig
from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction_fields import RecordExtractionFields
from swiss_ai_hub.agent.capabilities.record_extraction.sample_awaiting_confirmation import SampleAwaitingConfirmation
from swiss_ai_hub.agent.capabilities.record_extraction.selection_facets import SelectionFacets
from swiss_ai_hub.agent.i18n.agent_locale_handler import AgentLocaleHandler

T = AgentLocaleHandler("en")
FINANCE = BucketNamespacePair(bucket_name="finance-db", namespace_name="invoices")
LEGAL = BucketNamespacePair(bucket_name="legal-db", namespace_name="contracts")
PLANNER = "swiss_ai_hub.agent.capabilities.record_extraction.extraction_planner"
SAMPLE = "swiss_ai_hub.agent.capabilities.record_extraction.extraction_sample"
SCHEMA = RecordSchema(
    fields=[
        RecordField(name="item", type="string", description="The billed item."),
        RecordField(name="amount", type="number", description="The amount in CHF."),
    ]
)
OTHER_SCHEMA = RecordSchema(fields=[RecordField(name="supplier", type="string", description="Who billed.")])


class SampleConfig(RecordExtractionFields, AgentConfig):
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

    async def pop(self, key: str, default: Any = None) -> Any:
        return self.values.pop(key, default)

    async def set_if_absent(self, key: str, value: Any) -> bool:
        if key in self.values:
            return False
        self.values[key] = value
        return True


def _config(semantic: bool = False, **settings: Any) -> SampleConfig:
    return SampleConfig(
        agent_id="tables",
        name=LocaleString(en="Tables"),
        description=LocaleString(en="Tables fixture"),
        llm=LLMConfig(model_name="text-generation/main"),
        knowledge_documents=KnowledgeDocumentConfig(enabled=True, path_glob="invoices/**", semantic_search=semantic),
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


def _key(document: KnowledgeDocumentSummary) -> tuple[str, str, str]:
    return document.collection.bucket_name, document.collection.namespace_name, document.id


def _request(fields: str = "item, amount", **arguments: Any) -> ExtractRecordsEvent:
    selection = KnowledgeDocumentSelection(any_of=[KnowledgeDocumentCriteria(path_glob="invoices/**")])
    return ExtractRecordsEvent(selection=selection, fields=fields, collections=[FINANCE], **arguments)


def _displayer() -> MagicMock:
    displayer = MagicMock(spec=EventDisplayer)
    displayer.display_thought = AsyncMock()
    return displayer


def _schema_llm() -> Any:
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=MagicMock())
    context.__aexit__ = AsyncMock(return_value=None)
    return context


def _ranking(*documents: KnowledgeDocumentSummary) -> KnowledgeSemanticRanking:
    matches = [KnowledgeSemanticMatch(summary=document, score=1.0, passages=[]) for document in documents]
    return KnowledgeSemanticRanking(matches=matches, documents_in_scope=len(documents), unranked=0, capped=False)


class _Planning:
    """The planner with the selector, the schema model and the evidence scans stubbed."""

    def __init__(
        self,
        selected: KnowledgeDocumentSelectionResult | None = None,
        schema: RecordSchema = SCHEMA,
        matching: AsyncMock | None = None,
        rank: AsyncMock | None = None,
    ) -> None:
        self.resolve = AsyncMock(return_value=selected or KnowledgeDocumentSelectionResult(documents=[]))
        self.build = AsyncMock(return_value=schema)
        self.matching = matching or AsyncMock(return_value=set())
        self.rank = rank or AsyncMock(return_value=_ranking())
        self.displayer = _displayer()

    async def plan(
        self, request: ExtractRecordsEvent, config: SampleConfig, thread: _Thread
    ) -> list[DocumentExtractionRequestedEvent] | RecordsExtractedEvent:
        with (
            patch(f"{PLANNER}.KnowledgeDocumentSelector.resolve", self.resolve),
            patch(f"{PLANNER}.RecordSchemaBuilder.build", self.build),
            patch(f"{SAMPLE}.KnowledgeContentSearch.matching_ids", self.matching),
            patch(f"{SAMPLE}.KnowledgeSemanticSearch.rank", self.rank),
            patch.object(LLMConfig, "get_model_info", return_value={}),
            patch.object(LLMConfig, "cost_reporting_llm", return_value=_schema_llm()),
        ):
            return await ExtractionPlanner.plan(request, config, self.displayer, T, thread, None)

    def thoughts(self) -> list[str]:
        return [call.args[0] for call in self.displayer.display_thought.await_args_list]


def _no_rows(request: DocumentExtractionRequestedEvent) -> DocumentExtractedEvent:
    return DocumentExtractedEvent(run=request.run, request_event_id=request.event_id, document=request.document)


async def _assemble(planned: list[DocumentExtractionRequestedEvent]) -> RecordsExtractedEvent:
    with patch.object(ExtractionFileStore, "put_table", AsyncMock()):
        return await ExtractionTable.assemble(planned[0].run, [_no_rows(request) for request in planned], T)


class TestWhole:
    @pytest.mark.asyncio
    async def test_up_to_the_sample_threshold_every_document_is_extracted_in_one_answer(self):
        planning = _Planning(KnowledgeDocumentSelectionResult(documents=_documents(SAMPLE_ABOVE_DOCUMENTS)))
        thread = _Thread()

        planned = await planning.plan(_request(), _config(), thread)

        assert len(planned) == SAMPLE_ABOVE_DOCUMENTS
        assert [request.document.path for request in planned] == [doc.path for doc in _documents(100)]
        run = planned[0].run
        assert (run.sample, run.file_count, run.total_documents) == (False, 100, 0)
        assert planning.thoughts() == [
            "Extracting item, amount from 100 documents, about 5 minutes (path matches `invoices/**`)."
        ]
        planning.matching.assert_not_awaited()
        assert thread.values == {}

    @pytest.mark.asyncio
    async def test_a_whole_extraction_is_not_marked_as_awaiting_confirmation(self):
        planning = _Planning(KnowledgeDocumentSelectionResult(documents=_documents(3)))

        table = await _assemble(await planning.plan(_request(), _config(), _Thread()))

        assert table.awaiting_confirmation is False
        assert table.summary.startswith("**Files:** 3")


class TestSample:
    @pytest.mark.asyncio
    async def test_above_the_threshold_a_sample_is_extracted_and_the_selection_awaits_the_user(self):
        planning = _Planning(KnowledgeDocumentSelectionResult(documents=_documents(150)))
        thread = _Thread()
        request = _request(instructions="only hardware", document_terms="Hooli")

        planned = await planning.plan(request, _config(), thread)

        assert len(planned) == SAMPLE_DOCUMENTS
        run = planned[0].run
        assert (run.sample, run.total_documents, run.above_ceiling, run.file_count) == (True, 150, False, 5)
        assert any("**150 documents match.**" in notice for notice in run.notices)
        assert "**Columns:** item, amount · **Rows kept:** only hardware" in run.notices
        assert any(notice.startswith("**By folder:**") for notice in run.notices)
        assert "Reply *yes* to extract all 150 documents" in run.notices[-1]
        assert planning.thoughts()[0].startswith("150 documents match; extracting a sample from 5 of them")
        awaiting = await SampleAwaitingConfirmation.load(thread, "tables")
        assert awaiting is not None
        assert (awaiting.extraction_id, awaiting.total_documents, awaiting.record_schema) == (
            request.event_id,
            150,
            SCHEMA,
        )
        assert (awaiting.selection, awaiting.instructions, awaiting.document_terms) == (
            request.selection,
            "only hardware",
            "Hooli",
        )

    @pytest.mark.asyncio
    async def test_the_sample_answer_counts_against_the_whole_selection_and_awaits_confirmation(self):
        planning = _Planning(KnowledgeDocumentSelectionResult(documents=_documents(150)))

        table = await _assemble(await planning.plan(_request(), _config(), _Thread()))

        assert table.summary.startswith("**Sample:** 5 of 150 matching documents")
        assert table.awaiting_confirmation is True

    @pytest.mark.asyncio
    async def test_above_the_ceiling_only_narrowing_is_offered_and_nothing_awaits(self):
        thread = _Thread()
        await SampleAwaitingConfirmation.of(_request(), SCHEMA, 150).save(thread, "tables")
        planning = _Planning(KnowledgeDocumentSelectionResult(documents=_documents(12), truncated=True))

        planned = await planning.plan(_request(), _config(max_documents_total=12), thread)

        run = planned[0].run
        assert (run.sample, run.above_ceiling, len(planned)) == (True, True, 5)
        assert "**More than 12 documents match.**" in run.notices
        assert any("Please narrow the request" in notice for notice in run.notices)
        assert not any("Reply *yes*" in notice for notice in run.notices)
        assert "**By year in the path:** 2024, 2025" in run.notices
        assert await SampleAwaitingConfirmation.load(thread, "tables") is None
        table = await _assemble(planned)
        assert table.summary.startswith("**Sample:** 5 of more than 12 matching documents")
        assert table.awaiting_confirmation is False

    @pytest.mark.asyncio
    async def test_a_new_request_replaces_the_sample_awaiting_confirmation(self):
        thread = _Thread()
        await _Planning(KnowledgeDocumentSelectionResult(documents=_documents(150))).plan(_request(), _config(), thread)
        replacing = _request(fields="supplier")

        await _Planning(KnowledgeDocumentSelectionResult(documents=_documents(150))).plan(replacing, _config(), thread)
        replaced = await SampleAwaitingConfirmation.load(thread, "tables")
        await _Planning(KnowledgeDocumentSelectionResult(documents=_documents(2))).plan(_request(), _config(), thread)

        assert (replaced.extraction_id, replaced.fields) == (replacing.event_id, "supplier")
        assert await SampleAwaitingConfirmation.load(thread, "tables") is None

    @pytest.mark.asyncio
    async def test_a_new_request_that_finds_nothing_still_voids_the_earlier_sample(self):
        thread = _Thread()
        await _Planning(KnowledgeDocumentSelectionResult(documents=_documents(150))).plan(_request(), _config(), thread)

        await _Planning().plan(_request(fields="supplier"), _config(), thread)

        assert await SampleAwaitingConfirmation.load(thread, "tables") is None

    @pytest.mark.asyncio
    async def test_a_sample_waits_for_the_profile_that_showed_it_only(self):
        thread = _Thread()
        await _Planning(KnowledgeDocumentSelectionResult(documents=_documents(150))).plan(_request(), _config(), thread)
        other = _config().model_copy(update={"agent_id": "other-tables"})

        answer = await _Planning().plan(RecordExtraction.confirm_sample([FINANCE]), other, thread)

        assert answer.summary == T("agent.record_extraction.summary.nothing_awaiting")
        assert await SampleAwaitingConfirmation.load(thread, "tables") is not None

    def test_the_sample_spreads_over_the_largest_folders(self):
        sample = SelectionFacets.sample(_documents(12), 3)

        assert len({document.path.rsplit("/", 1)[0] for document in sample}) == 3

    def test_documents_with_evidence_lead_the_sample_and_the_rest_is_spread(self):
        documents = _documents(20)
        ordered = [documents[7], *(document for document in documents if document is not documents[7])]

        sample = ExtractionSample.pick(ordered, size=4, likely=1)

        assert sample[0] is documents[7]
        assert len(sample) == 4
        assert len({document.path for document in sample}) == 4


class TestConfirming:
    @pytest.mark.asyncio
    async def test_a_confirmation_extracts_every_document_with_the_samples_columns(self):
        thread = _Thread()
        documents = _documents(150)
        request = _request(instructions="only hardware", row_terms="Laptop")
        await _Planning(KnowledgeDocumentSelectionResult(documents=documents)).plan(request, _config(), thread)
        confirming = _Planning(KnowledgeDocumentSelectionResult(documents=documents), schema=OTHER_SCHEMA)

        planned = await confirming.plan(RecordExtraction.confirm_sample([FINANCE], ["note"]), _config(), thread)

        assert len(planned) == 150
        assert {request.document.path for request in planned} == {document.path for document in documents}
        confirming.build.assert_not_awaited()
        assert confirming.resolve.await_args.args[1] == request.selection
        assert all(planned_request.record_schema == SCHEMA for planned_request in planned)
        assert (planned[0].instructions, planned[0].row_terms) == ("only hardware", "Laptop")
        run = planned[0].run
        assert (run.sample, run.file_count, run.field_names, run.notices) == (False, 150, ["item", "amount"], ["note"])
        assert confirming.thoughts()[0].startswith("Extracting item, amount from 150 documents")
        assert await SampleAwaitingConfirmation.load(thread, "tables") is None

    @pytest.mark.asyncio
    async def test_a_confirmed_sample_still_says_the_search_behind_it_stopped_early(self):
        thread = _Thread()
        documents = _documents(150)
        sampled = _request(cut_short=True, notices=["The search stopped early."])
        await _Planning(KnowledgeDocumentSelectionResult(documents=documents)).plan(sampled, _config(), thread)

        planned = await _Planning(KnowledgeDocumentSelectionResult(documents=documents)).plan(
            RecordExtraction.confirm_sample([FINANCE], ["Scope note."]), _config(), thread
        )

        assert planned[0].run.cut_short is True
        assert planned[0].run.notices == ["Scope note.", "The search stopped early."]

    @pytest.mark.asyncio
    async def test_a_confirmation_reads_documents_with_evidence_first(self):
        thread = _Thread()
        documents = _documents(150)
        await _Planning(KnowledgeDocumentSelectionResult(documents=documents)).plan(
            _request(document_terms="Hooli"), _config(), thread
        )
        matching = AsyncMock(return_value={_key(documents[120])})
        confirming = _Planning(KnowledgeDocumentSelectionResult(documents=documents), matching=matching)

        planned = await confirming.plan(RecordExtraction.confirm_sample([FINANCE]), _config(), thread)

        assert planned[0].document.path == documents[120].path
        assert len(planned) == 150

    @pytest.mark.asyncio
    async def test_a_confirmation_without_a_sample_says_there_is_nothing_to_go_on_with(self):
        planning = _Planning()

        answer = await planning.plan(RecordExtraction.confirm_sample([FINANCE]), _config(), _Thread())

        assert isinstance(answer, RecordsExtractedEvent)
        assert answer.summary == T("agent.record_extraction.summary.nothing_awaiting")
        planning.resolve.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_a_confirmation_that_may_no_longer_read_the_sampled_collection_extracts_nothing(self):
        thread = _Thread()
        await _Planning(KnowledgeDocumentSelectionResult(documents=_documents(150))).plan(_request(), _config(), thread)
        confirming = _Planning(KnowledgeDocumentSelectionResult(documents=_documents(150)))

        answer = await confirming.plan(RecordExtraction.confirm_sample([LEGAL]), _config(), thread)

        assert isinstance(answer, RecordsExtractedEvent)
        assert answer.summary == T("agent.record_extraction.summary.scope_changed")
        confirming.resolve.assert_not_awaited()
        assert await SampleAwaitingConfirmation.load(thread, "tables") is None

    @pytest.mark.asyncio
    async def test_a_confirmation_answers_its_own_tool_call(self):
        thread = _Thread()
        await _Planning(KnowledgeDocumentSelectionResult(documents=_documents(150))).plan(_request(), _config(), thread)
        confirm = RecordExtraction.confirm_sample([FINANCE]).model_copy(update={"tool_call_id": "c2"})

        planned = await _Planning(KnowledgeDocumentSelectionResult(documents=_documents(150))).plan(
            confirm, _config(), thread
        )

        assert planned[0].run.tool_call_id == "c2"
        assert planned[0].run.extraction_id == confirm.event_id


class TestEvidence:
    @pytest.mark.asyncio
    async def test_documents_naming_the_wanted_ones_come_first_then_those_with_wanted_lines(self):
        documents = _documents(150)

        async def matching(collections, terms, budget, is_regex=False, path_globs=None):
            return {"Hooli": {_key(documents[140])}, "Laptop": {_key(documents[141]), _key(documents[140])}}[terms]

        scan = AsyncMock(side_effect=matching)
        with patch(f"{SAMPLE}.KnowledgeContentSearch.matching_ids", scan):
            ordered, likely = await ExtractionSample.ordered(documents, [FINANCE], "Hooli", "Laptop")

        assert likely == 2
        assert ordered[:2] == [documents[140], documents[141]]
        assert ordered[2:] == [document for document in documents if document not in ordered[:2]]
        assert all(call.kwargs["is_regex"] for call in scan.await_args_list)

    @pytest.mark.asyncio
    async def test_the_sample_of_a_large_selection_starts_with_the_documents_with_evidence(self):
        documents = _documents(150)
        planning = _Planning(
            KnowledgeDocumentSelectionResult(documents=documents),
            matching=AsyncMock(return_value={_key(documents[99]), _key(documents[3])}),
        )

        planned = await planning.plan(_request(document_terms="Hooli"), _config(), _Thread())

        assert [request.document.path for request in planned[:2]] == [documents[3].path, documents[99].path]
        assert len(planned) == SAMPLE_DOCUMENTS

    @pytest.mark.asyncio
    async def test_an_invalid_pattern_is_searched_as_literal_text(self):
        document = _documents(1)[0]
        scan = AsyncMock(side_effect=[InvalidSearchPatternError("Hooli (", "unbalanced"), {_key(document)}])
        with patch(f"{SAMPLE}.KnowledgeContentSearch.matching_ids", scan):
            ordered, likely = await ExtractionSample.ordered([document], [FINANCE], "Hooli (", None)

        assert (ordered, likely) == ([document], 1)
        assert [call.kwargs.get("is_regex", False) for call in scan.await_args_list] == [True, False]
        assert scan.await_args_list[1].args[1] == "Hooli ("

    @pytest.mark.asyncio
    async def test_a_scan_that_times_out_leaves_the_order(self):
        documents = _documents(10)
        scan = AsyncMock(side_effect=KnowledgeContentSearchTimeoutError(15.0))
        with patch(f"{SAMPLE}.KnowledgeContentSearch.matching_ids", scan):
            ordered, likely = await ExtractionSample.ordered(documents, [FINANCE], "Hooli", "Laptop")

        assert (ordered, likely) == (documents, 0)

    @pytest.mark.asyncio
    async def test_without_terms_nothing_is_scanned(self):
        documents = _documents(3)
        scan = AsyncMock()
        with patch(f"{SAMPLE}.KnowledgeContentSearch.matching_ids", scan):
            ordered, likely = await ExtractionSample.ordered(documents, [FINANCE], None, "  ")

        assert (ordered, likely) == (documents, 0)
        scan.assert_not_awaited()


class TestRankingByMeaning:
    @pytest.mark.asyncio
    async def test_the_ranking_decides_the_order_over_lexical_evidence_and_unranked_documents_follow(self):
        documents = _documents(10)
        rank = AsyncMock(return_value=_ranking(documents[7], documents[3]))
        scan = AsyncMock(return_value={_key(documents[5])})
        with (
            patch(f"{SAMPLE}.KnowledgeSemanticSearch.rank", rank),
            patch(f"{SAMPLE}.KnowledgeContentSearch.matching_ids", scan),
        ):
            ordered, likely = await ExtractionSample.ordered(
                documents, [FINANCE], "Hooli", None, semantic_query="Hooli hardware"
            )

        assert likely == 2
        assert ordered[:2] == [documents[7], documents[3]]
        assert ordered[2:] == [document for index, document in enumerate(documents) if index not in (3, 7)]
        assert rank.await_args.args[:2] == ([FINANCE], "Hooli hardware")
        scan.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_an_unavailable_ranking_falls_back_to_the_terms(self):
        documents = _documents(10)
        rank = AsyncMock(side_effect=KnowledgeSemanticSearchUnavailableError("milvus down"))
        scan = AsyncMock(return_value={_key(documents[5])})
        with (
            patch(f"{SAMPLE}.KnowledgeSemanticSearch.rank", rank),
            patch(f"{SAMPLE}.KnowledgeContentSearch.matching_ids", scan),
        ):
            ordered, likely = await ExtractionSample.ordered(
                documents, [FINANCE], "Hooli", None, semantic_query="Hooli hardware"
            )

        assert (ordered[0], likely) == (documents[5], 1)

    @pytest.mark.asyncio
    async def test_a_ranking_that_ran_out_of_time_leaves_the_term_scans_their_own_budget(self):
        documents = _documents(10)

        async def exhausting(*_args: Any, budget: KnowledgeSearchBudget, **_kwargs: Any) -> None:
            budget._deadline = 0.0
            raise budget.exhausted()

        scan = AsyncMock(return_value={_key(documents[5])})
        with (
            patch(f"{SAMPLE}.KnowledgeSemanticSearch.rank", exhausting),
            patch(f"{SAMPLE}.KnowledgeContentSearch.matching_ids", scan),
        ):
            ordered, likely = await ExtractionSample.ordered(
                documents, [FINANCE], "Hooli", None, semantic_query="Hooli hardware"
            )

        assert (ordered[0], likely) == (documents[5], 1)
        assert all(call.args[2].remaining_seconds() > 0 for call in scan.await_args_list)

    @pytest.mark.asyncio
    async def test_the_profiles_semantic_search_orders_even_a_small_selection_by_the_request(self):
        documents = _documents(4)
        planning = _Planning(
            KnowledgeDocumentSelectionResult(documents=documents), rank=AsyncMock(return_value=_ranking(documents[2]))
        )

        planned = await planning.plan(
            _request(document_terms="Hooli", instructions="only hardware"), _config(semantic=True), _Thread()
        )

        assert planned[0].document.path == documents[2].path
        assert len(planned) == 4
        assert planning.rank.await_args.args[1] == "Hooli only hardware item, amount"

    @pytest.mark.asyncio
    async def test_the_sample_of_a_ranked_profile_comes_from_the_ranking(self):
        documents = _documents(150)
        planning = _Planning(
            KnowledgeDocumentSelectionResult(documents=documents),
            rank=AsyncMock(return_value=_ranking(*documents[140:145])),
        )

        planned = await planning.plan(_request(), _config(semantic=True), _Thread())

        assert [request.document.path for request in planned] == [doc.path for doc in documents[140:145]]
        assert planning.rank.await_args.kwargs["path_globs"] == ["invoices/**"]

    @pytest.mark.asyncio
    async def test_a_ranking_that_places_none_of_the_documents_leaves_the_order_to_the_term_scans(self):
        documents = _documents(150)
        outside = _document("archive/2019/old.pdf")
        planning = _Planning(
            KnowledgeDocumentSelectionResult(documents=documents),
            matching=AsyncMock(return_value={_key(documents[90])}),
            rank=AsyncMock(return_value=_ranking(outside)),
        )

        planned = await planning.plan(_request(document_terms="Hooli"), _config(semantic=True), _Thread())

        assert planned[0].document.path == documents[90].path

    @pytest.mark.parametrize("count", [4, 150])
    @pytest.mark.asyncio
    async def test_without_the_profiles_semantic_search_nothing_is_ranked(self, count: int):
        planning = _Planning(KnowledgeDocumentSelectionResult(documents=_documents(count)))

        await planning.plan(_request(document_terms="Hooli"), _config(), _Thread())

        planning.rank.assert_not_awaited()
        assert planning.matching.await_count == (1 if count > SAMPLE_ABOVE_DOCUMENTS else 0)


class TestEstimate:
    def test_a_spreadsheet_counts_as_more_than_its_one_page(self):
        sheet = _document("invoices/list.xlsx").model_copy(update={"file_type": "xlsx"})

        assert ExtractionEstimate.windows(sheet) > ExtractionEstimate.windows(_document("invoices/a.pdf"))

    def test_the_minutes_grow_with_the_pages_and_shrink_with_parallel_calls(self):
        documents = [_document(f"invoices/{index}.pdf", pages=25) for index in range(48)]

        assert ExtractionEstimate.minutes(documents, parallel=1) == 40
        assert ExtractionEstimate.minutes(documents, parallel=4) == 10
