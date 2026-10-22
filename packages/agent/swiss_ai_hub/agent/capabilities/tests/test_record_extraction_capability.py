"""One table across many knowledge documents: documents are extracted in parallel and joined per extraction, a
document that fails is listed rather than fatal, and the table names the file of every row."""

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
    ExtractedTableMarkup,
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
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_table import ExtractionTable
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
SCHEMA = RecordSchema(
    fields=[
        RecordField(name="item", type="string", description="The billed item."),
        RecordField(name="amount", type="number", description="The amount in CHF."),
    ]
)


class TableConfig(RecordExtractionFields, AgentConfig):
    pass


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
    run: ExtractionRun, path: str, rows: list[dict[str, Any]] | None = None, **fields: Any
) -> DocumentExtractedEvent:
    return DocumentExtractedEvent(
        run=run, request_event_id=f"req-{run.extraction_id}-{path}", document=_summary(path), rows=rows or [], **fields
    )


def _selection() -> KnowledgeDocumentSelection:
    return KnowledgeDocumentSelection(any_of=[KnowledgeDocumentCriteria(path_glob="invoices/2025/**")])


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
    def test_every_row_names_its_file_and_the_table_is_marked(self):
        run = _run()
        results = [
            _result(run, "invoices/b.pdf", [{"item": "Laptop", "amount": 900}]),
            _result(run, "invoices/a.pdf", [{"item": "Rack", "amount": 1200}, {"item": "Cable", "amount": 20}]),
        ]

        table = ExtractionTable.assemble(run, results, max_rows=100, t=T)[0]

        assert table.columns == ["Path", "File", "Item", "Amount"]
        assert table.table.startswith('[aihub-extracted-table]: # "rows=3"')
        rows = [line for line in table.table.splitlines() if line.startswith("| invoices")]
        assert rows == [
            "| invoices/a.pdf | a.pdf | Rack | 1200 |",
            "| invoices/a.pdf | a.pdf | Cable | 20 |",
            "| invoices/b.pdf | b.pdf | Laptop | 900 |",
        ]
        assert (table.file_count, table.row_count, table.truncated) == (2, 3, False)

    def test_a_document_without_rows_counts_as_extracted_not_failed(self):
        run = _run()
        results = [_result(run, "a.pdf", [{"item": "Rack", "amount": 1}]), _result(run, "b.pdf", [])]

        table = ExtractionTable.assemble(run, results, max_rows=100, t=T)[0]

        assert (table.file_count, table.failed_count, table.row_count) == (2, 0, 1)

    def test_failed_files_are_listed_under_the_table(self):
        run = _run()
        results = [_result(run, "a.pdf", [{"item": "Rack", "amount": 1}]), _result(run, "b.pdf", failure_reason="boom")]

        table = ExtractionTable.assemble(run, results, max_rows=100, t=T)[0]

        assert table.failed_count == 1
        assert "- b.pdf: boom" in table.summary

    def test_the_row_limit_shows_the_first_rows_and_keeps_the_rest(self):
        run = _run(file_count=1)
        rows = [{"item": f"item {index}", "amount": index} for index in range(5)]

        table, overflow = ExtractionTable.assemble(run, [_result(run, "a.pdf", rows)], max_rows=2, t=T)

        assert (table.row_count, table.total_row_count) == (2, 5)
        assert len(overflow) == 3
        assert "item 2" in overflow[0]

    def test_cells_cannot_break_the_table(self):
        run = _run(file_count=1)

        table = ExtractionTable.assemble(run, [_result(run, "a.pdf", [{"item": "a|b\nc", "amount": None}])], 10, T)[0]

        assert "| a.pdf | a.pdf | a\\|b c |  |" in table.table

    def test_a_table_spanning_collections_names_each_rows_collection(self):
        run = _run(file_count=1, show_collection=True)

        table = ExtractionTable.assemble(run, [_result(run, "a.pdf", [{"item": "x", "amount": 1}])], 10, T)[0]

        assert table.columns[0] == "Collection"
        assert "| finance-db/invoices | a.pdf |" in table.table

    def test_the_marked_table_condenses_for_later_turns(self):
        run = _run(file_count=1)
        table = ExtractionTable.assemble(run, [_result(run, "a.pdf", [{"item": "x", "amount": 1}])], 10, T)[0]

        assert ExtractedTableMarkup.condensed(table.table) == "[A table of 1 extracted rows was shown here.]"


def _request(path: str = "invoices/2025/a.pdf") -> DocumentExtractionRequestedEvent:
    return DocumentExtractionRequestedEvent(run=_run(file_count=1), document=_summary(path), record_schema=SCHEMA)


def _displayer() -> MagicMock:
    displayer = MagicMock(spec=EventDisplayer)
    displayer.display_thought = AsyncMock()
    return displayer


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


def _redis() -> MagicMock:
    redis = MagicMock()
    redis.incr = AsyncMock(return_value=1)
    redis.expire = AsyncMock()
    return redis


def _loaded(text: str) -> KnowledgeDocument:
    return KnowledgeDocument(
        summary=_summary("invoices/2025/a.pdf"), text=text, text_length=len(text), start=0, end=len(text)
    )


class TestDocumentExtraction:
    @pytest.mark.asyncio
    async def test_a_long_document_is_read_in_part_and_its_rows_say_so(self):
        provenance = RecordProvenance.from_summary(_summary("invoices/2025/a.pdf"))
        extracted = DocumentExtractionResult.succeeded(provenance, [{"item": "Rack", "amount": 1.0}], 31, partial=True)
        extract = AsyncMock(return_value=extracted)
        llm_config = MagicMock()
        llm_config.cost_reporting_llm.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
        llm_config.cost_reporting_llm.return_value.__aexit__ = AsyncMock(return_value=None)
        displayer = _displayer()
        with (
            patch(f"{EXTRACTION}.KnowledgeDocumentReader.load_document", AsyncMock(return_value=_loaded("x" * 2000))),
            patch(f"{EXTRACTION}.RecordExtractor.extract", extract),
            patch.object(TableConfig, "extraction_llm", return_value=llm_config),
        ):
            result = await DocumentRecordExtraction.extract(
                _request(), _config(max_document_chars=1000), displayer, T, _redis(), None
            )
        run = _run(file_count=1)
        table, _ = ExtractionTable.assemble(run, [result.model_copy(update={"run": run})], 10, T)

        assert result.failure_reason is None
        assert result.partly_read
        assert extract.await_args.kwargs["max_windows"] == 12
        assert "a.pdf (partly read)" in table.table
        assert "**Partly read (rows may be missing):** invoices/2025/a.pdf" in table.summary
        assert "is long: reading only its relevant parts" in displayer.display_thought.await_args_list[0].args[0]

    @pytest.mark.asyncio
    async def test_any_error_becomes_the_documents_failure(self):
        displayer = _displayer()
        with patch(f"{EXTRACTION}.KnowledgeDocumentReader.load_document", AsyncMock(side_effect=RuntimeError("down"))):
            result = await DocumentRecordExtraction.extract(_request(), _config(), displayer, T, _redis(), None)

        assert result.failure_reason == "RuntimeError: down"
        displayer.display_thought.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_rows_come_back_with_long_cells_cut(self):
        provenance = RecordProvenance.from_summary(_summary("invoices/2025/a.pdf"))
        extracted = DocumentExtractionResult.succeeded(
            provenance, [{"item": "y" * 2000, "amount": 1.5}, {"item": "z" * 1000, "amount": 2.0}], 1
        )
        llm_config = MagicMock()
        llm_config.cost_reporting_llm.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
        llm_config.cost_reporting_llm.return_value.__aexit__ = AsyncMock(return_value=None)
        with (
            patch(f"{EXTRACTION}.KnowledgeDocumentReader.load_document", AsyncMock(return_value=_loaded("text"))),
            patch(f"{EXTRACTION}.RecordExtractor.extract", AsyncMock(return_value=extracted)),
            patch.object(TableConfig, "extraction_llm", return_value=llm_config),
        ):
            result = await DocumentRecordExtraction.extract(_request(), _config(), _displayer(), T, _redis(), None)

        assert result.failure_reason is None
        assert len(result.rows[0]["item"]) == 1000
        assert result.rows[0]["item"].endswith("…")
        assert result.rows[1]["item"] == "z" * 1000
        assert result.rows[0]["amount"] == 1.5


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
            planned = await ExtractionPlanner.plan(_extract_request(), _config(), displayer, T, _Thread(), None)

        assert resolve.await_args.args[2:4] == (1000, "invoices/**")
        assert [request.document.path for request in planned] == ["invoices/2025/a.pdf", "invoices/2025/b.pdf"]
        run = planned[0].run
        assert (run.file_count, run.field_names, run.show_collection, run.cut_short, run.sample) == (
            2,
            ["item", "amount"],
            True,
            False,
            False,
        )
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
                _extract_request(tool_call_id="c1"), _config(), _displayer(), T, _Thread(), None
            )

        assert isinstance(answer, RecordsExtractedEvent)
        assert answer.tool_call_id == "c1"
        assert "No document matches" in answer.summary
        build.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_a_problem_the_user_can_act_on_answers_instead_of_failing_the_run(self):
        resolve = AsyncMock(side_effect=ValueError("glob is empty"))
        with patch(f"{PLANNER}.KnowledgeDocumentSelector.resolve", resolve):
            answer = await ExtractionPlanner.plan(_extract_request(), _config(), _displayer(), T, _Thread(), None)

        assert answer.summary.startswith("The table could not be extracted: glob is empty")


def _decided(*call_ids: str) -> ToolCallsDecidedEvent:
    state = ToolLoopState(messages=[], mode=ToolLoopMode.ANSWER)
    return ToolCallsDecidedEvent(state=state, tool_call_ids=list(call_ids))


class TestAsATool:
    @pytest.mark.asyncio
    async def test_a_chosen_extraction_runs_over_the_collections_of_the_run(self):
        call = ToolCallApprovedEvent(
            tool_call_id="c1",
            name="extract_records",
            arguments={"any_of": [{"path_glob": "invoices/**"}], "fields": "item, amount", "instructions": "hardware"},
            kind="capability",
        )
        scope = KnowledgeDocumentRunScope(
            collections=[KnowledgeDocumentCollection(identifier="finance/invoices", collection=FINANCE, label="F")]
        )
        with patch(
            "swiss_ai_hub.agent.capabilities.record_extraction.record_extraction.KnowledgeDocumentScope.of",
            return_value=scope,
        ):
            request = await RecordExtraction.extract_tool_call_step(
                MagicMock(), call=call, request=RunToolLoopEvent(), tool=_config(), t=T, run_context=_Thread()
            )

        assert isinstance(request, ExtractRecordsEvent)
        assert (request.tool_call_id, request.collections, request.instructions) == ("c1", [FINANCE], "hardware")

    @pytest.mark.asyncio
    async def test_invalid_arguments_go_back_to_the_model(self):
        call = ToolCallApprovedEvent(
            tool_call_id="c1", name="extract_records", arguments={"fields": ""}, kind="capability"
        )

        result = await RecordExtraction.extract_tool_call_step(
            MagicMock(), call=call, request=RunToolLoopEvent(), tool=_config(), t=T, run_context=_Thread()
        )

        assert result.is_error
        assert "Invalid arguments" in result.content

    @pytest.mark.asyncio
    async def test_a_continuation_flag_given_as_text_still_continues_and_needs_no_selection(self):
        call = ToolCallApprovedEvent(
            tool_call_id="c1", name="extract_records", arguments={"continue_pending": "true"}, kind="capability"
        )
        scope = KnowledgeDocumentRunScope(
            collections=[KnowledgeDocumentCollection(identifier="finance/invoices", collection=FINANCE, label="F")]
        )
        with patch(
            "swiss_ai_hub.agent.capabilities.record_extraction.record_extraction.KnowledgeDocumentScope.of",
            return_value=scope,
        ):
            request = await RecordExtraction.extract_tool_call_step(
                MagicMock(), call=call, request=RunToolLoopEvent(), tool=_config(), t=T, run_context=_Thread()
            )

        assert isinstance(request, ExtractRecordsEvent)
        assert request.continue_pending

    @pytest.mark.asyncio
    async def test_a_new_extraction_without_documents_goes_back_to_the_model(self):
        call = ToolCallApprovedEvent(
            tool_call_id="c1", name="extract_records", arguments={"fields": "item, amount"}, kind="capability"
        )

        result = await RecordExtraction.extract_tool_call_step(
            MagicMock(), call=call, request=RunToolLoopEvent(), tool=_config(), t=T, run_context=_Thread()
        )

        assert result.is_error
        assert "needs any_of and fields" in result.content

    @pytest.mark.asyncio
    async def test_one_answer_continues_one_part_and_leaves_the_next_to_the_user(self):
        run_context = _Thread()
        scope = KnowledgeDocumentRunScope(
            collections=[KnowledgeDocumentCollection(identifier="finance/invoices", collection=FINANCE, label="F")]
        )

        async def continue_with(call_id: str) -> ExtractRecordsEvent | ToolResultEvent:
            call = ToolCallApprovedEvent(
                tool_call_id=call_id, name="extract_records", arguments={"continue_pending": True}, kind="capability"
            )
            with patch(
                "swiss_ai_hub.agent.capabilities.record_extraction.record_extraction.KnowledgeDocumentScope.of",
                return_value=scope,
            ):
                return await RecordExtraction.extract_tool_call_step(
                    MagicMock(), call=call, request=RunToolLoopEvent(), tool=_config(), t=T, run_context=run_context
                )

        first, redelivered, second = await continue_with("c1"), await continue_with("c1"), await continue_with("c2")

        assert isinstance(first, ExtractRecordsEvent)
        assert first.continue_pending
        assert isinstance(redelivered, ExtractRecordsEvent)
        assert isinstance(second, ToolResultEvent)
        assert "the rest waits for the user" in second.content

    @pytest.mark.asyncio
    async def test_a_sample_uses_up_the_answer_so_continuing_waits_for_the_user(self):
        run_context = _Thread()
        sample = RecordsExtractedEvent(
            extraction_id="x", summary="s", table="| a |", row_count=1, tool_call_id="c1", remaining_documents=40
        )
        await RecordExtraction.extract_tool_result_step(
            MagicMock(), extracted=sample, decided=_decided("c1"), run_context=run_context
        )
        call = ToolCallApprovedEvent(
            tool_call_id="c2", name="extract_records", arguments={"continue_pending": True}, kind="capability"
        )
        scope = KnowledgeDocumentRunScope(
            collections=[KnowledgeDocumentCollection(identifier="finance/invoices", collection=FINANCE, label="F")]
        )
        with patch(
            "swiss_ai_hub.agent.capabilities.record_extraction.record_extraction.KnowledgeDocumentScope.of",
            return_value=scope,
        ):
            refused = await RecordExtraction.extract_tool_call_step(
                MagicMock(), call=call, request=RunToolLoopEvent(), tool=_config(), t=T, run_context=run_context
            )

        assert isinstance(refused, ToolResultEvent)
        assert "the rest waits for the user" in refused.content

    @pytest.mark.asyncio
    async def test_a_complete_extraction_leaves_continuing_open(self):
        run_context = _Thread()
        whole = RecordsExtractedEvent(extraction_id="x", summary="s", table="| a |", row_count=1, tool_call_id="c1")

        await RecordExtraction.extract_tool_result_step(
            MagicMock(), extracted=whole, decided=_decided("c1"), run_context=run_context
        )

        assert run_context.values == {}

    @pytest.mark.asyncio
    async def test_the_model_reads_the_summary_and_is_told_not_to_retype_the_table(self):
        run = _run(file_count=1, tool_call_id="c1")
        table = ExtractionTable.assemble(run, [_result(run, "a.pdf", [{"item": "x", "amount": 1}])], 10, T)[0]

        assert await answers_an_extraction_call(table, _decided("c1"))
        result = await RecordExtraction.extract_tool_result_step(
            MagicMock(), extracted=table, decided=_decided("c1"), run_context=_Thread()
        )

        assert result.tool_call_id == "c1"
        assert "Do not write a table" in result.content
        assert "| a.pdf | a.pdf | x | 1 |" in result.content

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
