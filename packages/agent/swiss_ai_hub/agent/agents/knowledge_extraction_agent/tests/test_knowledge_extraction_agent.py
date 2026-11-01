"""The Knowledge Extraction Agent reads every document in the profile's scope by default, narrowed only by the places
the user names, or, with discovery, lets the model find the documents; it extracts within the profile's limits, a "yes"
to a sample extracts the whole selection, and it answers with the table; whatever goes wrong before a table exists
ends in a clear answer."""

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
from swiss_ai_hub.core.form import Checkbox
from swiss_ai_hub.core.generative_ai import (
    BucketNamespacePair,
    ExtractedTableMarkup,
    KnowledgeDocumentCriteria,
    KnowledgeDocumentListing,
    KnowledgeDocumentSelection,
    KnowledgeDocumentSummary,
    LLMConfig,
    RecordField,
    RecordSchema,
)
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.testing.auth_utils import fake_user

from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_answer import ROWS_PER_CHUNK
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_answer import ExtractionRequestAnswer
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_form import ExtractionRequestForm
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_form_request_event import (
    ExtractionRequestFormRequestEvent,
)
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_form_response_event import (
    ExtractionRequestFormResponseEvent,
)
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_plain_answer import (
    ExtractionRequestPlainAnswer,
)
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_reading import ExtractionRequestReading
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.knowledge_extraction_agent import KnowledgeExtractionAgent
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.knowledge_extraction_agent_config import (
    KnowledgeExtractionAgentConfig,
)
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.requested_location import RequestedLocation
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.selection_call import SelectionCall
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_collection import (
    KnowledgeDocumentCollection,
)
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_config import KnowledgeDocumentConfig
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_run_scope import (
    KnowledgeDocumentRunScope,
)
from swiss_ai_hub.agent.capabilities.record_extraction.extract_records_arguments import ExtractRecordsArguments
from swiss_ai_hub.agent.capabilities.record_extraction.sample_awaiting_confirmation import SampleAwaitingConfirmation
from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop_config import ToolLoopConfig
from swiss_ai_hub.agent.i18n.agent_locale_handler import AgentLocaleHandler

T = AgentLocaleHandler("en")
SCOPE_OF = "swiss_ai_hub.agent.agents.knowledge_extraction_agent.knowledge_extraction_agent.KnowledgeDocumentScope.of"
FINANCE = BucketNamespacePair(bucket_name="finance-db", namespace_name="invoices")
CONTRACTS = KnowledgeReference(database="legal", namespace="contracts")
SELECT = "select_knowledge_documents"
WHOLE = "swiss_ai_hub.agent.agents.knowledge_extraction_agent.whole_scope_request"


def _discovering(discovery: bool) -> KnowledgeDocumentConfig:
    return KnowledgeDocumentConfig(enabled=True, narrow_references=True, discovery=discovery)


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

    async def pop(self, key: str, default: Any = None) -> Any:
        return self.values.pop(key, default)

    async def set_if_absent(self, key: str, value: Any) -> bool:
        if key in self.values:
            return False
        self.values[key] = value
        return True


def _decided(iteration: int, *call_ids: str) -> ToolCallsDecidedEvent:
    state = ToolLoopState(messages=[], mode=ToolLoopMode.GATHER, iteration=iteration)
    return ToolCallsDecidedEvent(state=state, tool_call_ids=list(call_ids))


def test_the_blueprint_validates_and_offers_the_document_tools_and_the_selection():
    KnowledgeExtractionAgent.validate_workflow(KnowledgeExtractionAgentConfig)

    assert KnowledgeExtractionAgent.tools.names() == [
        "list_knowledge_documents",
        "search_knowledge_content",
        "read_knowledge_document",
        "rank_knowledge_documents",
        SELECT,
    ]
    assert "continue_extraction" not in KnowledgeExtractionAgent.tools.names()


def test_the_profile_form_fixes_the_document_tools_on_and_narrowing():
    form = KnowledgeExtractionAgentConfig.as_form()

    assert form.knowledge_documents.enabled is True
    assert form.knowledge_documents.narrow_references is True
    assert form.knowledge_tool.every_readable_collection is False
    assert isinstance(form.knowledge_documents.discovery, Checkbox)
    assert _config().knowledge_documents.discovery is False
    assert "discovery" not in KnowledgeExtractionAgentConfig.model_fields
    assert KnowledgeDocumentConfig.as_form().discovery is False


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
        request = await KnowledgeExtractionAgent().contextualize_step(event, agent_config=_config(), t=T)

    head = request.history[0].content
    assert "finance/invoices (Finance); only paths matching 'invoices/**'" in head
    assert head.index("select_knowledge_documents") < head.index("Client prompt.")
    assert request.history[2].content == "[A table of 7 extracted rows was shown here.]\n\nSummary"


@pytest.mark.asyncio
async def test_a_follow_up_keeps_the_request_it_refers_to_behind_a_long_answer_when_no_input_limit_is_set():
    long_answer = "| item | amount |\n" + "| Laptop X1 Carbon with docking station | 1900.00 |\n" * 400
    event = _event(
        ChatMessage(role=MessageRole.USER, content="Hardware lines on the 2025 Acme bills: item, amount."),
        ChatMessage(role=MessageRole.ASSISTANT, content=long_answer),
        ChatMessage(role=MessageRole.USER, content="Now the same for 2024."),
    )

    with patch(SCOPE_OF, return_value=_scope()):
        request = await KnowledgeExtractionAgent().contextualize_step(event, agent_config=_config(), t=T)

    assert [message.content for message in request.history[1:]] == [
        "Hardware lines on the 2025 Acme bills: item, amount.",
        long_answer,
        "Now the same for 2024.",
    ]


@pytest.mark.asyncio
async def test_the_model_is_told_to_search_exact_names_by_keyword_and_described_documents_by_meaning():
    with patch(SCOPE_OF, return_value=_scope()):
        request = await KnowledgeExtractionAgent().contextualize_step(
            _event(ChatMessage(role=MessageRole.USER, content="Liability caps")), agent_config=_config(), t=T
        )

    head = request.history[0].content
    assert "When it names exact things" in head
    assert "rank_knowledge_documents ranks every document in scope by meaning" in head
    assert "Start with rank_knowledge_documents" not in head
    assert "A ranking is not a filter" in head
    assert "exact keywords and semantic keywords" in head
    assert "Relevance is about the document, never about its rows" in head
    assert "only paths matching 'invoices/**'" in head


@pytest.mark.asyncio
async def test_without_a_readable_collection_the_agent_says_so_instead_of_looping():
    with patch(SCOPE_OF, return_value=_scope(empty=True)):
        answer = await KnowledgeExtractionAgent().discover_step(
            _ctx(),
            _event(),
            agent_config=_config(),
            displayer=_displayer(),
            t=T,
            thread=_Thread(),
            run_context=_Thread(),
        )

    assert isinstance(answer, CompleteConversationEvent)
    assert "no knowledge collection" in answer.stop.output_messages[-1].content


@pytest.mark.asyncio
async def test_with_discovery_the_confirmed_request_gathers_with_the_messages_references():
    loop, ask, _ = await _discover(_reading(), discovery=True)

    assert (loop.mode, loop.knowledge_references) == (ToolLoopMode.GATHER, [CONTRACTS])
    assert loop.hands_back_results is False
    assert [message.role for message in loop.history[-2:]] == [MessageRole.ASSISTANT, MessageRole.USER]
    assert "**Filter Condition:** only Hooli hardware" in loop.history[-1].content
    ask.assert_awaited_once()


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
            run_context=_Thread(),
            decided=[_decided(0, "c1")],
            calls=[_select("c1", "invoices/2025/**")],
            results=[_result("c1")],
        )

    assert isinstance(request, ExtractRecordsEvent)
    assert (request.fields, request.instructions, request.collections) == ("item, amount", "only hardware", [FINANCE])
    assert request.cut_short is True
    assert any("stopped at its limit" in notice for notice in request.notices)
    assert any("legal/contracts" in notice for notice in request.notices)


@pytest.mark.asyncio
async def test_the_confirmed_exact_keywords_order_the_documents_when_the_selection_names_none():
    run_context = _Thread()
    await ExtractionRequestForm.confirm(run_context, _reading(calculation="the sum of all amounts"))
    with patch(SCOPE_OF, return_value=_scope()):
        request = await KnowledgeExtractionAgent().plan_step(
            ToolLoopFinishedEvent(stopped_early=False),
            _ctx(),
            _event(),
            agent_config=_config(),
            displayer=_displayer(),
            t=T,
            run_context=run_context,
            decided=[_decided(0, "c1")],
            calls=[_select("c1", "invoices/2025/**")],
            results=[_result("c1")],
        )

    assert request.document_terms == "Hooli"
    assert request.notices[0].startswith("I don't calculate the sum of all amounts.")


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
            run_context=_Thread(),
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
            run_context=_Thread(),
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
            run_context=_Thread(),
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


def _reading(
    *locations: RequestedLocation,
    is_table_request: bool = True,
    confirms_sample: bool = False,
    calculation: str | None = None,
    document_kind: str | None = None,
) -> ExtractionRequestAnswer:
    return ExtractionRequestAnswer(
        is_table_request=is_table_request,
        confirms_sample=confirms_sample,
        locations=list(locations),
        fields="item, amount",
        instructions="only Hooli hardware",
        calculation=calculation,
        document_kind=document_kind,
        row_terms="Laptop|Server",
        document_terms="Hooli",
    )


FOLDER = "invoices/einvoices/zugferd"
NAMED = "zugferd_2p0_EXTENDED_Warenrechnung.pdf"
NAMED_FILES = (
    f"{FOLDER}/{NAMED}",
    f"{FOLDER}/EN16931_Einfach.pdf",
    "invoices/acme/acme invoice 42.pdf",
    "invoices/Rechnung.pdf",
)


def _listing(*paths: str) -> KnowledgeDocumentListing:
    documents = [
        _document(path).model_copy(update={"collection": FINANCE})
        for path in paths
        or ("invoices/2024/q1/a.pdf", "invoices/2024/q2/b.pdf", "invoices/2025/q1/c.pdf", "other/2026/d.pdf")
    ]
    return KnowledgeDocumentListing.from_summaries(documents)


async def _awaiting(thread: _Thread) -> None:
    request = ExtractRecordsEvent(
        selection=KnowledgeDocumentSelection(any_of=[KnowledgeDocumentCriteria()]),
        fields="item, amount",
        collections=[FINANCE],
    )
    schema = RecordSchema(fields=[RecordField(name="item", type="string", description="The billed item.")])
    await SampleAwaitingConfirmation.of(request, schema, 150).save(thread, "extraction-test")


AS_UNDERSTOOD = json.dumps({key: {"type": "option", "option_index": 0} for key in ("where", "rows", "columns")})


async def _discover(
    reading: ExtractionRequestAnswer | None,
    *,
    discovery: bool = False,
    thread: _Thread | None = None,
    listing: KnowledgeDocumentListing | None = None,
    scope: KnowledgeDocumentRunScope | None = None,
    message: str = "Hooli hardware",
    answer: str | None = AS_UNDERSTOOD,
    reread: ExtractionRequestAnswer | None = None,
) -> tuple[Any, AsyncMock, AsyncMock]:
    """The discover step, and, when it asks the request form, the confirm step with the given answer."""
    ask = AsyncMock(side_effect=[reading, reread])
    list_documents = AsyncMock(return_value=listing or _listing())
    ctx = ConversationContextualizedEvent(history=[ChatMessage(role=MessageRole.USER, content=message)], query=message)
    run_context = _Thread()
    with (
        patch(SCOPE_OF, return_value=scope or _scope()),
        patch(f"{WHOLE}.ExtractionRequestReading.ask", ask),
        patch(f"{WHOLE}.KnowledgeDocumentReader.list_documents", list_documents),
    ):
        step = await KnowledgeExtractionAgent().discover_step(
            ctx,
            _event(),
            agent_config=_config(knowledge_documents=_discovering(discovery)),
            displayer=_displayer(),
            t=T,
            thread=thread or _Thread(),
            run_context=run_context,
        )
        if isinstance(step, ExtractionRequestFormRequestEvent) and answer is not None:
            response = ExtractionRequestFormResponseEvent(response=answer, request_event=step)
            step = await KnowledgeExtractionAgent().confirm_request_step(
                response,
                ctx,
                _event(),
                agent_config=_config(knowledge_documents=_discovering(discovery)),
                displayer=_displayer(),
                t=T,
                run_context=run_context,
            )
    return step, ask, list_documents


class TestWholeScope:
    @pytest.mark.asyncio
    async def test_without_discovery_every_document_in_scope_is_extracted_with_the_requests_reading(self):
        request, ask, list_documents = await _discover(_reading(), scope=_scope(ignored=[CONTRACTS]))

        assert isinstance(request, ExtractRecordsEvent)
        assert request.selection == KnowledgeDocumentSelection(any_of=[KnowledgeDocumentCriteria()])
        assert (request.fields, request.instructions, request.row_terms, request.document_terms) == (
            "item, amount",
            "only Hooli hardware",
            "Laptop|Server",
            "Hooli",
        )
        assert (request.collections, request.confirmed, request.cut_short) == ([FINANCE], False, False)
        assert any("legal/contracts" in notice for notice in request.notices)
        assert list_documents.await_args.args[0] == [FINANCE]
        assert ask.await_args.args[4] is False
        assert any(line.startswith("**By folder:**") for line in ask.await_args.args[2])

    @pytest.mark.asyncio
    async def test_a_named_place_narrows_the_scope_by_path(self):
        location = RequestedLocation(path_glob="invoices/2025/**", path_regex=None)

        request, _, _ = await _discover(_reading(location))

        assert request.selection.any_of == [KnowledgeDocumentCriteria(path_glob="invoices/2025/**")]

    @pytest.mark.asyncio
    async def test_several_named_places_select_any_of_them(self):
        locations = [
            RequestedLocation(path_glob="invoices/2025/**", path_regex=None),
            RequestedLocation(path_glob=None, path_regex="2024"),
        ]

        request, _, _ = await _discover(_reading(*locations))

        assert request.selection.any_of == [
            KnowledgeDocumentCriteria(path_glob="invoices/2025/**"),
            KnowledgeDocumentCriteria(path_regex="2024"),
        ]

    @pytest.mark.asyncio
    async def test_a_named_place_without_documents_answers_with_the_scopes_folders(self):
        location = RequestedLocation(path_glob="invoices/2026/**", path_regex=None)

        answer, _, _ = await _discover(_reading(location))

        assert isinstance(answer, CompleteConversationEvent)
        text = answer.stop.output_messages[-1].content
        assert text.startswith("No document in this agent's scope is at `invoices/2026/**`, so nothing was extracted.")
        assert "**By folder:** invoices/2024/q1 (1), invoices/2024/q2 (1), invoices/2025/q1 (1)" in text

    @pytest.mark.asyncio
    async def test_a_file_path_the_model_read_as_a_topic_is_still_where_the_rows_come_from(self):
        message = "List the requirements in invoices/2025/q1/c.pdf. Columns: id, requirement."

        request, _, _ = await _discover(_reading(), message=message)

        assert request.selection.any_of == [KnowledgeDocumentCriteria(path_glob="**/invoices/2025/q1/c.pdf")]

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("message", "folder", "glob"),
        [
            (f"Line items of {FOLDER}/{NAMED}?", FOLDER, f"**/{FOLDER}/{NAMED}"),
            (f"Line items of {NAMED}?", FOLDER, f"**/{NAMED}"),
            ("Line items of zugferd_2p0_EXTENDED_Warenrechnung, please.", FOLDER, f"**/{NAMED}"),
            ("Line items of ZUGFERD_2p0_extended_warenrechnung.PDF", FOLDER, f"**/{NAMED}"),
            ("Line items of acme invoice 42.pdf.", "invoices/acme", "**/acme invoice 42.pdf"),
        ],
        ids=["full-path", "name", "name-without-extension", "other-case", "name-with-spaces"],
    )
    async def test_a_named_file_wins_over_the_folder_the_reading_made_of_it(self, message: str, folder: str, glob: str):
        """Real invoices: Kimi read `einvoices/zugferd/x.pdf` as `einvoices/zugferd/**` and 81 rows came back for 6."""
        reading = _reading(RequestedLocation(path_glob=f"{folder}/**", path_regex=None))

        request, _, _ = await _discover(reading, message=message, listing=_listing(*NAMED_FILES))

        assert request.selection.any_of == [KnowledgeDocumentCriteria(path_glob=glob)]

    @pytest.mark.asyncio
    async def test_another_place_the_user_named_next_to_the_file_is_kept(self):
        reading = _reading(
            RequestedLocation(path_glob=f"{FOLDER}/**", path_regex=None),
            RequestedLocation(path_glob="invoices/acme/**", path_regex=None),
        )

        request, _, _ = await _discover(reading, message=f"{NAMED} and the acme folder", listing=_listing(*NAMED_FILES))

        assert request.selection.any_of == [
            KnowledgeDocumentCriteria(path_glob=f"**/{NAMED}"),
            KnowledgeDocumentCriteria(path_glob="invoices/acme/**"),
        ]

    @pytest.mark.asyncio
    async def test_a_reading_of_the_exact_file_is_not_doubled(self):
        reading = _reading(RequestedLocation(path_glob=f"**/{NAMED}", path_regex=None))

        request, _, _ = await _discover(reading, message=f"Items of {NAMED}", listing=_listing(*NAMED_FILES))

        assert request.selection.any_of == [KnowledgeDocumentCriteria(path_glob=f"**/{NAMED}")]

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "message",
        ["List all Rechnung totals.", "Items of unknown_2024.pdf"],
        ids=["plain-word-stem", "name-of-no-document"],
    )
    async def test_a_word_that_names_no_file_in_scope_leaves_the_whole_scope(self, message: str):
        request, _, _ = await _discover(_reading(), message=message, listing=_listing(*NAMED_FILES))

        assert request.selection.any_of == [KnowledgeDocumentCriteria()]

    @pytest.mark.asyncio
    async def test_a_name_shared_by_two_folders_reads_both_files(self):
        listing = _listing("invoices/a/x-1.pdf", "invoices/b/x-1.pdf", "invoices/b/y.pdf")

        request, _, _ = await _discover(_reading(), message="Rows of x-1.pdf", listing=listing)

        assert request.selection.any_of == [KnowledgeDocumentCriteria(path_glob="**/x-1.pdf")]
        assert len(listing.matching_glob("**/x-1.pdf").documents) == 2

    @pytest.mark.asyncio
    async def test_the_last_folders_of_a_path_find_the_document_they_end(self):
        request, _, _ = await _discover(_reading(), message="Requirements in /q1/c.pdf, please.")

        assert request.selection.any_of == [KnowledgeDocumentCriteria(path_glob="**/q1/c.pdf")]

    @pytest.mark.asyncio
    async def test_a_written_file_path_outside_the_scope_is_reported_not_replaced_by_one_of_the_same_name(self):
        message = "List the requirements in alpha/2025/q1/c.pdf. Columns: id, requirement."

        answer, _, _ = await _discover(_reading(), message=message)

        assert isinstance(answer, CompleteConversationEvent)
        assert "is at `**/alpha/2025/q1/c.pdf`" in answer.stop.output_messages[-1].content

    @pytest.mark.asyncio
    async def test_a_place_outside_the_profiles_glob_holds_nothing(self):
        location = RequestedLocation(path_glob="other/**", path_regex=None)

        answer, _, _ = await _discover(_reading(location))

        assert isinstance(answer, CompleteConversationEvent)
        assert "is at `other/**`" in answer.stop.output_messages[-1].content
        assert "other/2026" not in answer.stop.output_messages[-1].content

    @pytest.mark.asyncio
    async def test_an_invalid_path_pattern_is_left_to_the_extraction_to_report(self):
        location = RequestedLocation(path_glob=None, path_regex="(unclosed")

        request, _, _ = await _discover(_reading(location))

        assert isinstance(request, ExtractRecordsEvent)
        assert request.selection.any_of == [KnowledgeDocumentCriteria(path_regex="(unclosed")]

    @pytest.mark.asyncio
    async def test_a_message_that_asks_for_no_table_is_told_what_the_agent_does(self):
        answer, _, _ = await _discover(_reading(is_table_request=False))

        assert isinstance(answer, CompleteConversationEvent)
        assert answer.stop.output_messages[-1].content == T(
            "agent.knowledge_extraction_agent.messages.not_a_table_request"
        )

    @pytest.mark.asyncio
    async def test_a_model_that_read_no_usable_request_asks_for_one(self):
        answer, _, _ = await _discover(None)

        assert isinstance(answer, CompleteConversationEvent)
        assert answer.stop.output_messages[-1].content == T("agent.knowledge_extraction_agent.messages.no_request")

    @pytest.mark.asyncio
    async def test_a_yes_while_a_sample_awaits_confirms_it(self):
        thread = _Thread()
        await _awaiting(thread)

        request, ask, _ = await _discover(_reading(confirms_sample=True), thread=thread)

        assert isinstance(request, ExtractRecordsEvent)
        assert (request.confirmed, request.selection, request.collections) == (True, None, [FINANCE])
        assert ask.await_args.args[4] is True

    @pytest.mark.asyncio
    async def test_a_confirmation_without_a_sample_is_read_as_a_new_request(self):
        request, _, _ = await _discover(_reading(confirms_sample=True))

        assert isinstance(request, ExtractRecordsEvent)
        assert request.confirmed is False
        assert request.selection is not None


def _dialog(**answers: dict[str, Any]) -> str:
    return json.dumps({"where": {"type": "option", "option_index": 0}, **answers})


class TestRequestForm:
    @pytest.mark.asyncio
    async def test_the_request_is_asked_back_as_three_questions_and_as_text(self):
        form, ask, _ = await _discover(_reading(), answer=None)

        assert isinstance(form, ExtractionRequestFormRequestEvent)
        assert form.hitl_type == "chat"
        assert form.topic.event_name == "ExtractionRequestFormResponseEvent"
        where, rows, columns = form.questions
        assert [option.label for option in where.options] == ["All documents"]
        assert [option.label for option in rows.options] == ["As understood", "Every row"]
        assert rows.options[0].description == "only Hooli hardware"
        assert [(option.label, option.description) for option in columns.options] == [("As understood", "item, amount")]
        assert all(question.allow_other for question in form.questions)
        assert [question.header for question in form.questions] == ["Location", "Filter Condition", "Values to extract"]
        assert where.question == (
            "Which documents should I read? I understood: all documents in scope. To read only some, name a folder, a "
            "file or a year. Folders: invoices/2024/q1 (1), invoices/2024/q2 (1), invoices/2025/q1 (1)"
        )
        assert rows.question.endswith(
            "A condition on the records, not a calculation, e.g. from Lieferant GmbH · dated 2018 · "
            "only hardware items."
        )
        assert "→ one row per invoice; item, quantity, net amount → one row per line item." in columns.question
        assert "- **Filter Condition:** only Hooli hardware" in form.question
        reply, location, condition, values = form.question.split("\n")[-4:]
        assert reply == "Reply *yes* to go ahead, or write what to change:"
        assert location == f"- **Location:** {where.question.split('scope. ')[1]}"
        assert condition.endswith(rows.question.split("Hooli hardware. ")[1])
        assert values.startswith("- **Values to extract:** The values decide what a row is")
        ask.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_a_long_folder_list_is_cut_at_the_end_of_the_question(self):
        folders = [f"invoices/supplier-with-a-long-name-{index:02d}/x.pdf" for index in range(12)]

        form, _, _ = await _discover(
            _reading(calculation="the sum of all invoices"), answer=None, listing=_listing(*folders)
        )

        where = form.questions[0].question
        assert len(where) == 500
        assert where.startswith("I don't calculate the sum of all invoices.")
        assert "Folders: invoices/supplier-with-a-long-name-" in where
        assert where.endswith("…")

    @pytest.mark.asyncio
    async def test_a_named_place_can_be_kept_or_dropped(self):
        location = RequestedLocation(path_glob="invoices/2025/**", path_regex=None)

        form, _, _ = await _discover(_reading(location), answer=None)

        assert [(option.label, option.description) for option in form.questions[0].options] == [
            ("As understood", "invoices/2025/**"),
            ("All documents", "Read every document in this agent's scope"),
        ]

    @pytest.mark.asyncio
    async def test_as_understood_extracts_the_reading_without_reading_again(self):
        request, ask, _ = await _discover(_reading())

        assert isinstance(request, ExtractRecordsEvent)
        assert request.instructions == "only Hooli hardware"
        ask.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_the_second_options_drop_the_place_and_the_row_condition(self):
        location = RequestedLocation(path_glob="invoices/2025/**", path_regex=None)
        answer = json.dumps(
            {"where": {"type": "option", "option_index": 1}, "rows": {"type": "option", "option_index": 1}}
        )

        request, ask, _ = await _discover(_reading(location), answer=answer)

        assert request.selection == KnowledgeDocumentSelection(any_of=[KnowledgeDocumentCriteria()])
        assert request.instructions is None
        ask.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_a_written_answer_is_read_once_more_with_the_form_before_it(self):
        reread = _reading().model_copy(update={"instructions": "only invoices dated June 2018"})
        answer = _dialog(rows={"type": "other", "text": "only invoices dated June 2018"})

        request, ask, _ = await _discover(_reading(), answer=answer, reread=reread)

        assert request.instructions == "only invoices dated June 2018"
        history = ask.await_args_list[1].args[0]
        assert history[-2].role == MessageRole.ASSISTANT
        assert "- **Filter Condition:** only Hooli hardware" in history[-2].content
        assert history[-1].content.splitlines() == [
            "**Location:** all documents in scope",
            "**Filter Condition:** only invoices dated June 2018",
            "**Values to extract:** item, amount",
        ]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("reply", ["yes", "Ja!", " ok. "])
    async def test_a_typed_yes_keeps_the_reading(self, reply: str):
        request, ask, _ = await _discover(_reading(), answer=reply)

        assert request.instructions == "only Hooli hardware"
        ask.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_a_typed_correction_is_read_once_more(self):
        reread = _reading().model_copy(update={"fields": "item, amount, date"})

        request, ask, _ = await _discover(_reading(), answer="add the date column", reread=reread)

        assert request.fields == "item, amount, date"
        assert ask.await_args_list[1].args[0][-1].content == "add the date column"

    @pytest.mark.asyncio
    async def test_a_calculation_is_named_first_in_the_form_and_under_the_table(self):
        notice = T("agent.knowledge_extraction_agent.form.calculation_notice", calculation="the sum of all invoices")
        reading = _reading(calculation="the sum of all invoices")

        form, _, _ = await _discover(reading, answer=None)
        request, ask, _ = await _discover(reading)

        assert notice.startswith("I don't calculate the sum of all invoices.")
        assert form.question.startswith(f"{notice}\n")
        assert form.questions[0].question.startswith(f"{notice} Which documents should I read?")
        assert not form.questions[1].question.startswith(notice)
        assert request.notices[0] == notice
        ask.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_without_a_calculation_neither_the_form_nor_the_table_names_one(self):
        form, _, _ = await _discover(_reading(), answer=None)
        request, _, _ = await _discover(_reading())

        assert form.question.startswith("Before I read the documents")
        assert form.questions[0].question.startswith("Which documents should I read?")
        assert not any("calculate" in notice for notice in request.notices)

    @pytest.mark.asyncio
    async def test_with_discovery_the_form_also_asks_the_exact_and_the_semantic_keywords(self):
        reading = _reading(document_kind="supplier invoice with line items")

        form, _, _ = await _discover(reading, discovery=True, answer=None)

        assert [question.header for question in form.questions] == [
            "Location",
            "Filter Condition",
            "Values to extract",
            "Exact keyword(s)",
            "Semantic keyword(s)",
        ]
        exact, semantic = form.questions[3:]
        assert [(option.label, option.description) for option in exact.options] == [
            ("As understood", "Hooli"),
            ("None", "Let the search decide"),
        ]
        assert semantic.options[0].description == "supplier invoice with line items"
        assert "Lieferant GmbH" in exact.question
        assert "- **Semantic keyword(s):** supplier invoice with line items" in form.question

    @pytest.mark.asyncio
    async def test_keywords_the_request_did_not_name_offer_none_first(self):
        reading = _reading().model_copy(update={"document_terms": None})

        form, _, _ = await _discover(reading, discovery=True, answer=None)

        assert [option.label for option in form.questions[3].options] == ["None"]
        assert [option.label for option in form.questions[4].options] == ["None"]

    @pytest.mark.asyncio
    async def test_without_discovery_the_form_asks_three_parts(self):
        form, _, _ = await _discover(_reading(document_kind="supplier invoice"), answer=None)

        assert len(form.questions) == 3

    @pytest.mark.asyncio
    async def test_none_on_both_keywords_lets_the_search_decide(self):
        answer = _dialog(
            rows={"type": "option", "option_index": 0},
            columns={"type": "option", "option_index": 0},
            exact={"type": "option", "option_index": 1},
            semantic={"type": "option", "option_index": 1},
        )

        loop, ask, _ = await _discover(_reading(document_kind="invoice"), discovery=True, answer=answer)

        assert loop.mode == ToolLoopMode.GATHER
        assert loop.history[-1].content.splitlines()[-2:] == [
            "**Exact keyword(s):** none",
            "**Semantic keyword(s):** none",
        ]
        ask.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_written_keywords_reach_the_search_as_written(self):
        answer = _dialog(
            exact={"type": "other", "text": "Lieferant GmbH"},
            semantic={"type": "other", "text": "supplier invoice"},
        )

        loop, _, _ = await _discover(_reading(), discovery=True, answer=answer)

        assert "**Exact keyword(s):** Lieferant GmbH" in loop.history[-1].content
        assert "**Semantic keyword(s):** supplier invoice" in loop.history[-1].content

    @pytest.mark.asyncio
    async def test_a_correction_the_model_cannot_read_asks_for_a_request(self):
        answer, _, _ = await _discover(_reading(), answer="hmm", reread=None)

        assert isinstance(answer, CompleteConversationEvent)
        assert answer.stop.output_messages[-1].content == T("agent.knowledge_extraction_agent.messages.no_request")


@pytest.mark.parametrize(
    ("message", "globs"),
    [
        ("List the requirements in alpha/specs/requirements.md.", ["**/alpha/specs/requirements.md"]),
        ("Rows of /invoices/x.pdf and (q1/c.pdf), twice: q1/c.pdf", ["**/invoices/x.pdf", "**/q1/c.pdf"]),
        ("See https://example.com/docs/a.pdf for the format", []),
        ("and/or the 2025 invoices from v1.2/notes", []),
        ("x/.pdf and a/b.verylongext", []),
        ("Columns from [the spec](docs/spec.md) and path=a/b.pdf", ["**/docs/spec.md", "**/a/b.pdf"]),
    ],
    ids=["sentence-end", "punctuation-and-duplicates", "url", "no-extension", "no-stem-or-long-extension", "glued"],
)
def test_the_paths_a_message_spells_out_are_read_word_by_word(message: str, globs: list[str]):
    assert [location.path_glob for location in RequestedLocation.written_in(message)] == globs


@pytest.mark.parametrize(
    ("message", "paths", "globs"),
    [
        ("Rows of report-2024.pdf", ["a/report-2024.pdf", "a/report-2024.docx"], ["**/report-2024.pdf"]),
        ("Rows of inv-12.pdf", ["a/inv-1.pdf"], []),
        ("Rows of a/inv-1.pdf", ["a/inv-1.pdf"], []),
        ("Rows of report [draft].pdf", ["a/report [draft].pdf"], ["**/report [[]draft].pdf"]),
        ("Rows of Rechnung", ["a/Rechnung.pdf"], []),
    ],
    ids=["other-extension", "longer-name", "written-path", "glob-characters", "plain-word"],
)
def test_the_names_a_message_holds_are_the_names_of_documents_in_scope(
    message: str, paths: list[str], globs: list[str]
):
    named = RequestedLocation.named_in(message, paths)

    assert [location.path_glob for location in named] == globs
    assert all(_listing(*paths).matching_glob(glob).documents for glob in globs)


def test_a_message_built_to_make_a_pattern_backtrack_is_read_at_once():
    message = "a/" * 20_000 + "b" * 20_000 + "!"

    assert RequestedLocation.written_in(message) == []


class TestDiscovery:
    @pytest.mark.asyncio
    async def test_with_discovery_a_yes_while_a_sample_awaits_still_confirms_it(self):
        thread = _Thread()
        await _awaiting(thread)

        request, ask, _ = await _discover(_reading(confirms_sample=True), discovery=True, thread=thread)

        assert isinstance(request, ExtractRecordsEvent)
        assert request.confirmed is True
        ask.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_with_discovery_a_new_request_while_a_sample_awaits_runs_the_loop(self):
        thread = _Thread()
        await _awaiting(thread)

        loop, ask, _ = await _discover(_reading(), discovery=True, thread=thread)

        assert loop.mode == ToolLoopMode.GATHER
        ask.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_with_discovery_an_unreadable_message_while_a_sample_awaits_asks_for_a_request(self):
        thread = _Thread()
        await _awaiting(thread)

        answer, _, _ = await _discover(None, discovery=True, thread=thread)

        assert isinstance(answer, CompleteConversationEvent)
        assert answer.stop.output_messages[-1].content == T("agent.knowledge_extraction_agent.messages.no_request")


class TestRequestReading:
    @staticmethod
    def _llm_config(predict: AsyncMock) -> MagicMock:
        llm = MagicMock()
        llm.model_copy.return_value.astructured_predict = predict
        llm_config = MagicMock()
        llm_config.cost_reporting_llm.return_value.__aenter__ = AsyncMock(return_value=llm)
        llm_config.cost_reporting_llm.return_value.__aexit__ = AsyncMock(return_value=None)
        return llm_config

    @pytest.mark.asyncio
    async def test_the_request_is_read_deterministically_with_the_conversation_before_it(self):
        predict = AsyncMock(return_value=_reading())
        llm_config = self._llm_config(predict)
        history = [
            ChatMessage(role=MessageRole.SYSTEM, content="Instructions."),
            ChatMessage(role=MessageRole.USER, content="Hardware on the 2025 invoices"),
            ChatMessage(role=MessageRole.ASSISTANT, content="Here is the sample."),
            ChatMessage(role=MessageRole.USER, content="yes"),
        ]

        reading = await ExtractionRequestReading.ask(
            history, _scope(), ["**By folder:** a (1)"], "Profile rule.", True, llm_config, _displayer(), None, T
        )

        assert reading == _reading()
        llm = llm_config.cost_reporting_llm.return_value.__aenter__.return_value
        assert llm.model_copy.call_args.kwargs["update"]["temperature"] == 0.0
        kwargs = predict.await_args.kwargs
        assert kwargs["request"] == "yes"
        assert kwargs["awaiting_sample"] is True
        assert kwargs["profile_instructions"] == "Profile rule."
        assert kwargs["facets"] == "**By folder:** a (1)"
        assert kwargs["conversation"] == "user: Hardware on the 2025 invoices\n\nassistant: Here is the sample."

    @pytest.mark.asyncio
    async def test_an_unusable_answer_is_none(self):
        llm_config = self._llm_config(AsyncMock(side_effect=ValueError("unterminated JSON")))

        reading = await ExtractionRequestReading.ask(
            [ChatMessage(role=MessageRole.USER, content="x")],
            _scope(),
            [],
            None,
            False,
            llm_config,
            _displayer(),
            None,
            T,
        )

        assert reading is None

    @pytest.mark.asyncio
    async def test_an_answer_cut_off_in_its_term_list_is_read_again_without_the_terms(self):
        plain = ExtractionRequestPlainAnswer(
            is_table_request=True,
            confirms_sample=False,
            locations=[],
            fields="item, amount",
            instructions="hardware",
            calculation=None,
            document_kind=None,
        )
        predict = AsyncMock(side_effect=[ValueError("EOF while parsing 'Drain|Sewer|Pipe|Tube|H"), plain])

        reading = await ExtractionRequestReading.ask(
            [ChatMessage(role=MessageRole.USER, content="Hardware lines")],
            _scope(),
            [],
            None,
            False,
            self._llm_config(predict),
            _displayer(),
            None,
            T,
        )

        assert [call.args[0] for call in predict.await_args_list] == [
            ExtractionRequestAnswer,
            ExtractionRequestPlainAnswer,
        ]
        assert reading == ExtractionRequestAnswer(
            is_table_request=True,
            confirms_sample=False,
            locations=[],
            fields="item, amount",
            instructions="hardware",
            calculation=None,
            document_kind=None,
            row_terms=None,
            document_terms=None,
        )

    @pytest.mark.parametrize(
        ("locale", "example"),
        [
            (
                "en",
                'Filter Condition: "sum all the items in the invoice", goes into calculation, never into instructions',
            ),
            (
                "de",
                'Filterbedingung: "summiere alle Positionen der Rechnung", gehört in calculation, nie in instructions',
            ),
            (
                "fr",
                'Condition de filtre : "additionne toutes les positions de la facture", va dans calculation, jamais',
            ),
            ("it", 'Condizione di filtro: "somma tutte le voci della fattura", va in calculation, mai in instructions'),
        ],
    )
    def test_a_calculation_written_into_the_form_is_read_as_a_calculation_not_a_condition(
        self, locale: str, example: str
    ):
        """Real invoices: "Sum all the items in the invoice" under Which rows became the row condition, and the
        extraction model summed item lines itself on 2 of 106 invoices instead of reading their printed totals."""
        prompt = AgentLocaleHandler(locale)("agent.knowledge_extraction_agent.prompt.read_request")

        assert example in prompt

    @pytest.mark.parametrize("locale", ["en", "de", "fr", "it"])
    def test_the_prompt_names_every_field_of_the_answer(self, locale: str):
        prompt = AgentLocaleHandler(locale)("agent.knowledge_extraction_agent.prompt.read_request")

        assert "calculation" in ExtractionRequestAnswer.model_fields
        for field in ExtractionRequestAnswer.model_fields:
            assert field in prompt
        for field in RequestedLocation.model_fields:
            assert field in prompt
