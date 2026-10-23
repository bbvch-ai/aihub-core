"""The Knowledge Extraction Agent lets the model find the documents, extracts from the ones it settled on within the
profile's limits, and answers with the table; whatever goes wrong before a table exists ends in a clear answer."""

import json
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    CompleteConversationEvent,
    ConversationContextualizedEvent,
    ExtractRecordsEvent,
    KnowledgeReference,
    LLMStopEvent,
    RecordsExtractedEvent,
    ToolCallApprovedEvent,
    ToolCallsDecidedEvent,
    ToolLoopFinishedEvent,
    ToolLoopMode,
    ToolLoopState,
    ToolResultEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.generative_ai import (
    BucketNamespacePair,
    ExtractedTableMarkup,
    KnowledgeDocumentCriteria,
    KnowledgeDocumentSummary,
    LLMConfig,
)
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.testing.auth_utils import fake_user

from swiss_ai_hub.agent.agents.knowledge_extraction_agent.continuation_tools import CONTINUE_EXTRACTION_TOOL
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_answer import ROWS_PER_CHUNK
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.knowledge_extraction_agent import KnowledgeExtractionAgent
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.knowledge_extraction_agent_config import (
    KnowledgeExtractionAgentConfig,
)
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.selection_call import SelectionCall
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_collection import (
    KnowledgeDocumentCollection,
)
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_run_scope import (
    KnowledgeDocumentRunScope,
)
from swiss_ai_hub.agent.capabilities.record_extraction.extract_records_arguments import ExtractRecordsArguments
from swiss_ai_hub.agent.capabilities.record_extraction.pending_extraction import PendingExtraction
from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop_config import ToolLoopConfig
from swiss_ai_hub.agent.i18n.agent_locale_handler import AgentLocaleHandler

T = AgentLocaleHandler("en")
SCOPE_OF = "swiss_ai_hub.agent.agents.knowledge_extraction_agent.knowledge_extraction_agent.KnowledgeDocumentScope.of"
FINANCE = BucketNamespacePair(bucket_name="finance-db", namespace_name="invoices")
CONTRACTS = KnowledgeReference(database="legal", namespace="contracts")
SELECT = "select_knowledge_documents"


def _config(**fields: Any) -> KnowledgeExtractionAgentConfig:
    return KnowledgeExtractionAgentConfig(
        agent_id="extraction-test",
        name=LocaleString(en="Extraction"),
        description=LocaleString(en="Extraction fixture"),
        llm=LLMConfig(model_name="text-generation/dummy"),
        **fields,
    )


def _scope(*, ignored: list[KnowledgeReference] | None = None, empty: bool = False) -> KnowledgeDocumentRunScope:
    collections = (
        []
        if empty
        else [KnowledgeDocumentCollection(identifier="finance/invoices", collection=FINANCE, label="Finance")]
    )
    return KnowledgeDocumentRunScope(collections=collections, restricting_glob="invoices/**", ignored=ignored or [])


def _event(*messages: ChatMessage) -> UserMessageEvent:
    return UserMessageEvent(messages=list(messages), user=fake_user(), locale="en", knowledge_references=[CONTRACTS])


def _ctx() -> ConversationContextualizedEvent:
    return ConversationContextualizedEvent(history=[], query="Hardware lines on the 2025 Acme bills")


def _displayer() -> MagicMock:
    displayer = MagicMock(spec=EventDisplayer)
    displayer.display_chunk = AsyncMock()
    return displayer


def _select(call_id: str, path_glob: str) -> ToolCallApprovedEvent:
    return ToolCallApprovedEvent(
        tool_call_id=call_id,
        name=SELECT,
        arguments={"any_of": [{"path_glob": path_glob}], "fields": "item, amount", "instructions": "only hardware"},
        kind="function",
    )


def _continue(call_id: str, user_agreed: bool = True) -> ToolCallApprovedEvent:
    return ToolCallApprovedEvent(
        tool_call_id=call_id, name=CONTINUE_EXTRACTION_TOOL, arguments={"user_agreed": user_agreed}, kind="function"
    )


def _result(call_id: str, is_error: bool = False, name: str = SELECT) -> ToolResultEvent:
    return ToolResultEvent(tool_call_id=call_id, name=name, content="Selected documents: 2.", is_error=is_error)


def _document(path: str) -> KnowledgeDocumentSummary:
    return KnowledgeDocumentSummary(
        id=path,
        collection=BucketNamespacePair(bucket_name="finance", namespace_name="invoices"),
        path=path,
        filename=path.rsplit("/", 1)[-1],
        title=path,
        file_type="pdf",
        updated_at=datetime(2025, 1, 1, tzinfo=UTC),
    )


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


def _decided(iteration: int, *call_ids: str) -> ToolCallsDecidedEvent:
    state = ToolLoopState(messages=[], mode=ToolLoopMode.GATHER, iteration=iteration)
    return ToolCallsDecidedEvent(state=state, tool_call_ids=list(call_ids))


def test_the_blueprint_validates_and_offers_the_document_tools_and_the_selection():
    KnowledgeExtractionAgent.validate_workflow(KnowledgeExtractionAgentConfig)

    assert KnowledgeExtractionAgent.tools.names() == [
        "list_knowledge_documents",
        "search_knowledge_content",
        "read_knowledge_document",
        SELECT,
        CONTINUE_EXTRACTION_TOOL,
    ]


def test_the_profile_form_fixes_the_document_tools_on_and_narrowing():
    form = KnowledgeExtractionAgentConfig.as_form()

    assert form.knowledge_documents.enabled is True
    assert form.knowledge_documents.narrow_references is True
    assert form.knowledge_tool.every_readable_collection is False


@pytest.mark.asyncio
async def test_the_instructions_name_the_scope_ahead_of_the_clients_prompt_and_earlier_tables_shrink():
    earlier = f"{ExtractedTableMarkup.wrap('| a |', rows=7)}\n\nSummary"
    event = _event(
        ChatMessage(role=MessageRole.SYSTEM, content="Client prompt."),
        ChatMessage(role=MessageRole.USER, content="first"),
        ChatMessage(role=MessageRole.ASSISTANT, content=earlier),
        ChatMessage(role=MessageRole.USER, content="same for 2024"),
    )

    with patch(SCOPE_OF, return_value=_scope()):
        request = await KnowledgeExtractionAgent().contextualize_step(
            event, agent_config=_config(), t=T, thread=_Thread()
        )

    head = request.history[0].content
    assert "finance/invoices (Finance); only paths matching 'invoices/**'" in head
    assert head.index("select_knowledge_documents") < head.index("Client prompt.")
    assert request.history[2].content == "[A table of 7 extracted rows was shown here.]\n\nSummary"


@pytest.mark.asyncio
async def test_without_a_readable_collection_the_agent_says_so_instead_of_looping():
    with patch(SCOPE_OF, return_value=_scope(empty=True)):
        answer = await KnowledgeExtractionAgent().discover_step(
            _ctx(), _event(), agent_config=_config(), displayer=_displayer(), t=T, thread=_Thread()
        )

    assert isinstance(answer, CompleteConversationEvent)
    assert "no knowledge collection" in answer.stop.output_messages[-1].content


@pytest.mark.asyncio
async def test_the_discovery_loop_gathers_with_the_messages_references():
    with patch(SCOPE_OF, return_value=_scope()):
        request = await KnowledgeExtractionAgent().discover_step(
            _ctx(), _event(), agent_config=_config(), displayer=_displayer(), t=T, thread=_Thread()
        )

    assert (request.mode, request.knowledge_references) == (ToolLoopMode.GATHER, [CONTRACTS])
    assert CONTINUE_EXTRACTION_TOOL not in request.tools


@pytest.mark.asyncio
async def test_an_unfinished_extraction_is_named_and_can_be_continued():
    thread = _Thread()
    await PendingExtraction(
        extraction_id="x1",
        documents=[_document(f"invoices/2025/{index}.pdf") for index in range(6)],
        part_starts=[0, 3],
        next_part=1,
        finished_parts=[0],
        criteria="path matches `invoices/2025/**`",
    ).save(thread)

    with patch(SCOPE_OF, return_value=_scope()):
        context = await KnowledgeExtractionAgent().contextualize_step(
            _event(ChatMessage(role=MessageRole.USER, content="weiter")), agent_config=_config(), t=T, thread=thread
        )
        loop = await KnowledgeExtractionAgent().discover_step(
            _ctx(), _event(), agent_config=_config(), displayer=_displayer(), t=T, thread=thread
        )

    assert "3 documents are still to extract" in context.history[0].content
    assert loop.tools is None


@pytest.mark.asyncio
async def test_continuing_extracts_the_next_part_instead_of_a_selection():
    decided = [_decided(0, "s1"), _decided(1, "c1")]
    calls = [_select("s1", "invoices/**"), _continue("c1")]
    results = [_result("s1"), _result("c1", name=CONTINUE_EXTRACTION_TOOL)]
    finished = ToolLoopFinishedEvent(loop="tools", block=[], stopped_early=False)

    with patch(SCOPE_OF, return_value=_scope()):
        request = await KnowledgeExtractionAgent().plan_step(
            finished,
            _ctx(),
            _event(),
            agent_config=_config(),
            displayer=_displayer(),
            t=T,
            decided=decided,
            calls=calls,
            results=results,
        )

    assert request.continue_pending is True
    assert request.selection is None


def test_a_continuation_the_user_did_not_agree_to_continues_nothing():
    decided = [_decided(0, "s1"), _decided(1, "c1")]
    calls = [_select("s1", "invoices/**"), _continue("c1", user_agreed=False)]
    results = [_result("s1"), _result("c1", name=CONTINUE_EXTRACTION_TOOL)]

    assert not SelectionCall.continued(decided, calls, results)
    assert SelectionCall.continued(decided, [_select("s1", "invoices/**"), _continue("c1")], results)


def test_the_last_successful_selection_wins_by_the_loops_own_order():
    calls = [_select("c1", "first/**"), _select("c2", "second/**"), _select("c3", "third/**")]
    decided = [_decided(0, "c1"), _decided(1, "c3", "c2")]
    results = [_result("c1"), _result("c2"), _result("c3", is_error=True)]

    selection = SelectionCall.last(decided, list(reversed(calls)), results)

    assert selection.any_of[0].path_glob == "second/**"


def test_no_successful_selection_is_none():
    assert SelectionCall.last([_decided(0, "c1")], [_select("c1", "x/**")], [_result("c1", is_error=True)]) is None
    assert SelectionCall.last(None, None, None) is None


@pytest.mark.asyncio
async def test_the_selection_is_extracted_with_the_users_fields_and_notices():
    finished = ToolLoopFinishedEvent(stopped_early=True)
    with patch(SCOPE_OF, return_value=_scope(ignored=[CONTRACTS])):
        request = await KnowledgeExtractionAgent().plan_step(
            finished,
            _ctx(),
            _event(),
            agent_config=_config(),
            displayer=_displayer(),
            t=T,
            decided=[_decided(0, "c1")],
            calls=[_select("c1", "invoices/2025/**")],
            results=[_result("c1")],
        )

    assert isinstance(request, ExtractRecordsEvent)
    assert (request.fields, request.instructions, request.collections) == ("item, amount", "only hardware", [FINANCE])
    assert request.cut_short is True
    assert any("stopped at its limit" in notice for notice in request.notices)
    assert any("legal/contracts" in notice for notice in request.notices)


@pytest.mark.parametrize(
    ("stopped_early", "tool_loop", "expected"),
    [
        (False, ToolLoopConfig(), "could not tell which documents"),
        (True, ToolLoopConfig(), "reached its limit"),
        (False, ToolLoopConfig(disable_tools=True, disabled_tools=[SELECT]), "switched off selecting"),
    ],
)
@pytest.mark.asyncio
async def test_no_selection_ends_with_why(stopped_early: bool, tool_loop: ToolLoopConfig, expected: str):
    with patch(SCOPE_OF, return_value=_scope()):
        answer = await KnowledgeExtractionAgent().plan_step(
            ToolLoopFinishedEvent(stopped_early=stopped_early),
            _ctx(),
            _event(),
            agent_config=_config(tool_loop=tool_loop),
            displayer=_displayer(),
            t=T,
        )

    assert expected in answer.stop.output_messages[-1].content


@pytest.mark.asyncio
async def test_the_table_is_streamed_in_parts_and_follow_ups_see_only_the_summary():
    rows = "\n".join(f"| a.pdf | row {index} |" for index in range(120))
    table = ExtractedTableMarkup.wrap(f"| Path | item |\n| --- | --- |\n{rows}", rows=120)
    extracted = RecordsExtractedEvent(extraction_id="x", table=table, summary="**Files:** 1", row_count=120)
    displayer = _displayer()

    request = await KnowledgeExtractionAgent().complete_step(extracted, _ctx(), displayer)

    streamed = "".join(call.args[0] for call in displayer.display_chunk.await_args_list)
    assert displayer.display_chunk.await_count == 4
    assert all(len(call.args[0].splitlines()) <= ROWS_PER_CHUNK + 1 for call in displayer.display_chunk.await_args_list)
    assert isinstance(request.stop, LLMStopEvent)
    assert request.stop.output_messages[-1].content == streamed
    assert streamed.endswith("**Files:** 1")
    assert request.answer.output_messages[-1].content == "**Files:** 1"


@pytest.mark.asyncio
async def test_a_model_that_searched_but_never_selected_is_asked_for_the_selection_once():
    from swiss_ai_hub.agent.capabilities.record_extraction.extract_records_arguments import ExtractRecordsArguments

    search = ToolCallApprovedEvent(
        tool_call_id="c1", name="search_knowledge_content", arguments={"query": "ACME AG"}, kind="function"
    )
    found = ToolResultEvent(tool_call_id="c1", name="search_knowledge_content", content="Documents 1-3 of 3 ...")
    stated = ExtractRecordsArguments(any_of=[{"content_query": "ACME AG"}], fields="item, amount")
    ask = AsyncMock(return_value=stated)
    with (
        patch(SCOPE_OF, return_value=_scope()),
        patch(
            "swiss_ai_hub.agent.agents.knowledge_extraction_agent.knowledge_extraction_agent.SelectionFallback.ask", ask
        ),
    ):
        request = await KnowledgeExtractionAgent().plan_step(
            ToolLoopFinishedEvent(),
            _ctx(),
            _event(),
            agent_config=_config(),
            displayer=_displayer(),
            t=T,
            decided=[_decided(0, "c1")],
            calls=[search],
            results=[found],
        )

    assert isinstance(request, ExtractRecordsEvent)
    assert request.selection.any_of[0].content_query == "ACME AG"
    assert ask.await_args.args[1:3] == ([search], [found])


def test_the_fallback_reads_every_search_with_its_result_once():
    from swiss_ai_hub.agent.agents.knowledge_extraction_agent.selection_fallback import SelectionFallback

    call = ToolCallApprovedEvent(
        tool_call_id="c1", name="list_knowledge_documents", arguments={"path_glob": "**"}, kind="function"
    )
    result = ToolResultEvent(tool_call_id="c1", name="list_knowledge_documents", content="x" * 2000)

    transcript = SelectionFallback._transcript([call, call], [result])

    assert transcript.count("list_knowledge_documents") == 1
    assert transcript.startswith('list_knowledge_documents({"path_glob": "**"}):')
    assert len(transcript) < 700


async def _stopped_search(selection: ExtractRecordsArguments | None) -> tuple[Any, AsyncMock]:
    search = ToolCallApprovedEvent(
        tool_call_id="c1", name="search_knowledge_content", arguments={"query": "liability"}, kind="function"
    )
    ask = AsyncMock(return_value=selection)
    with (
        patch(SCOPE_OF, return_value=_scope()),
        patch(
            "swiss_ai_hub.agent.agents.knowledge_extraction_agent.knowledge_extraction_agent.SelectionFallback.ask", ask
        ),
    ):
        answer = await KnowledgeExtractionAgent().plan_step(
            ToolLoopFinishedEvent(stopped_early=True),
            _ctx(),
            _event(),
            agent_config=_config(),
            displayer=_displayer(),
            t=T,
            calls=[search],
            results=[ToolResultEvent(tool_call_id="c1", name="search_knowledge_content", content="3 documents")],
        )
    return answer, ask


@pytest.mark.asyncio
async def test_a_search_stopped_at_its_limit_selects_by_folder_and_is_not_marked_incomplete():
    found = ExtractRecordsArguments(
        any_of=[{"path_glob": "contracts/**"}], fields="supplier, liability cap", instructions="cap below EUR 100k"
    )

    request, ask = await _stopped_search(found)

    ask.assert_awaited_once()
    assert ask.await_args.args[-1] is True
    assert isinstance(request, ExtractRecordsEvent)
    assert (request.instructions, request.cut_short) == ("cap below EUR 100k", False)
    assert any("selected by folder" in notice for notice in request.notices)
    assert not any("may be missing" in notice for notice in request.notices)


@pytest.mark.asyncio
async def test_a_stopped_search_that_found_nothing_still_says_so():
    answer, ask = await _stopped_search(None)

    ask.assert_awaited_once()
    assert "reached its limit" in answer.stop.output_messages[-1].content


async def _ask_fallback(answer: Any, stopped_early: bool = False) -> tuple[ExtractRecordsArguments | None, AsyncMock]:
    from swiss_ai_hub.agent.agents.knowledge_extraction_agent.selection_fallback import SelectionFallback

    predict = AsyncMock(return_value=answer)
    llm = MagicMock()
    llm.model_copy.return_value.astructured_predict = predict
    llm_config = MagicMock()
    llm_config.cost_reporting_llm.return_value.__aenter__ = AsyncMock(return_value=llm)
    llm_config.cost_reporting_llm.return_value.__aexit__ = AsyncMock(return_value=None)
    selection = await SelectionFallback.ask(
        "contracts with a liability cap below EUR 100,000",
        [_select("s1", "contracts/**")],
        [_result("s1")],
        _scope(),
        llm_config,
        _displayer(),
        None,
        T,
        stopped_early,
    )
    return selection, predict


@pytest.mark.asyncio
async def test_the_fallback_extracts_nothing_when_the_model_says_nothing_matches():
    from swiss_ai_hub.agent.agents.knowledge_extraction_agent.selection_fallback_answer import SelectionFallbackAnswer

    answer = SelectionFallbackAnswer(any_of=[{"content_query": "Umbrella"}], fields="item", nothing_matches=True)

    selection, _ = await _ask_fallback(answer)

    assert selection is None


def test_the_fallback_cannot_select_documents_by_the_ids_its_searches_showed():
    from swiss_ai_hub.agent.agents.knowledge_extraction_agent.selection_fallback_answer import SelectionFallbackAnswer

    schema = json.dumps(SelectionFallbackAnswer.model_json_schema())

    assert "document_ids" not in schema
    assert "content_query" in schema


@pytest.mark.parametrize(
    ("stopped_early", "expected"),
    [
        (False, KnowledgeDocumentCriteria(path_glob="contracts/**", content_query="Molina")),
        (True, KnowledgeDocumentCriteria(path_glob="contracts/**")),
    ],
)
@pytest.mark.asyncio
async def test_after_a_stopped_search_the_fallback_keeps_only_folders_and_paths(stopped_early: bool, expected: Any):
    from swiss_ai_hub.agent.agents.knowledge_extraction_agent.selection_fallback_answer import SelectionFallbackAnswer

    answer = SelectionFallbackAnswer(
        any_of=[{"path_glob": "contracts/**", "content_query": "Molina"}],
        fields="supplier, liability cap",
        instructions="cap below EUR 100,000",
    )

    selection, predict = await _ask_fallback(answer, stopped_early)

    assert selection is not None
    assert selection.any_of == [expected]
    assert selection.instructions == "cap below EUR 100,000"
    assert predict.await_args.kwargs["stopped"] is stopped_early


@pytest.mark.asyncio
async def test_a_stopped_search_without_a_folder_selects_every_document_in_scope():
    from swiss_ai_hub.agent.agents.knowledge_extraction_agent.selection_fallback_answer import SelectionFallbackAnswer

    answer = SelectionFallbackAnswer(any_of=[{"content_query": "liability cap"}], fields="supplier, liability cap")

    selection, _ = await _ask_fallback(answer, stopped_early=True)

    assert selection is not None
    assert selection.any_of == [KnowledgeDocumentCriteria()]


def test_the_fallback_prompt_asks_for_folders_only_after_a_stopped_search():
    from llama_index.core.prompts.rich import RichPromptTemplate

    prompt = RichPromptTemplate(T("agent.knowledge_extraction_agent.prompt.select_now"))
    rendered = {
        stopped: prompt.format(request="r", scope="s", transcript="t", stopped=stopped) for stopped in (False, True)
    }

    assert "Select by folder and path only" in rendered[True]
    assert "Select by folder and path only" not in rendered[False]
    assert "document_ids" not in rendered[True]
