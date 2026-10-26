"""The Universal Agent hands its instructed history to the conversation, lets the model work through every tool it
offers, and completes with the reply; nothing is loaded into the prompt up front."""

from unittest.mock import MagicMock

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent import (
    CompleteConversationEvent,
    ConversationContextualizedEvent,
    KnowledgeReference,
    LLMEvent,
    Message,
    ToolLoopFinishedEvent,
    UserMessageEvent,
    UserUploadedFile,
)
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.testing.auth_utils import fake_user

from swiss_ai_hub.agent.agents.universal_agent.universal_agent import UniversalAgent
from swiss_ai_hub.agent.agents.universal_agent.universal_agent_config import UniversalAgentConfig
from swiss_ai_hub.agent.capabilities.web_fetch.web_fetch_config import WebFetchConfig
from swiss_ai_hub.agent.i18n.agent_locale_handler import AgentLocaleHandler

T = AgentLocaleHandler("en")
REPORT = UserUploadedFile(
    filename="report.pdf", file_type="application/pdf", file_id="11111111-1111-4111-8111-111111111111"
)
POLICIES = KnowledgeReference(database="hr", namespace="policies")


def _config(**fields: object) -> UniversalAgentConfig:
    return UniversalAgentConfig(
        agent_id="universal-test",
        name=LocaleString(en="Universal"),
        description=LocaleString(en="Universal fixture"),
        llm=LLMConfig(model_name="text-generation/dummy"),
        **fields,
    )


def _message(*messages: ChatMessage) -> UserMessageEvent:
    return UserMessageEvent(
        messages=list(messages), user=fake_user(), locale="en", files=[REPORT], knowledge_references=[POLICIES]
    )


def test_the_blueprint_offers_knowledge_files_memory_web_pages_and_the_sandbox_in_one_loop():
    UniversalAgent.validate_workflow(UniversalAgentConfig)

    assert {capability.__name__ for capability in UniversalAgent.installed_capabilities()} == {
        "Conversation",
        "ToolLoop",
        "Knowledge",
        "AttachedFiles",
        "Memory",
        "WebFetch",
        "RecordExtraction",
    }
    assert UniversalAgent.tools.names() == [
        "search_knowledge",
        "read_attached_files",
        "recall_memory",
        "fetch_web_pages",
        "extract_records",
        "run_command",
        "get_process_status",
        "send_process_input",
        "kill_process",
        "list_processes",
        "list_files",
        "read_file",
        "write_file",
        "replace_file_content",
        "grep_search",
        "glob_search",
        "display_file",
        "list_my_files",
        "read_my_file",
        "list_knowledge_documents",
        "search_knowledge_content",
        "read_knowledge_document",
        "rank_knowledge_documents",
        "select_knowledge_documents",
    ]


@pytest.mark.asyncio
async def test_the_agents_instructions_lead_one_system_message_ahead_of_the_clients():
    event = _message(
        ChatMessage(role=MessageRole.SYSTEM, content="Client prompt."),
        ChatMessage(role=MessageRole.USER, content="Hi"),
    )

    request = await UniversalAgent().contextualize_step(
        event, agent_config=_config(instructions=LocaleString(en="Answer briefly.")), t=T
    )

    head = request.history[0]
    assert [message.role for message in request.history] == [MessageRole.SYSTEM, MessageRole.USER]
    assert head.content.startswith(T("agent.universal_agent.prompt.instructions"))
    assert head.content.index("Answer briefly.") < head.content.index("Client prompt.")


@pytest.mark.asyncio
async def test_the_pages_referenced_with_hash_are_named_in_the_instructions():
    """A `#` link is not in the message text, only in the tool's description; without this a model asked to
    summarise "this page" answered that it saw no link."""
    event = _message(ChatMessage(role=MessageRole.USER, content="Please summarize this page"))
    event.web_references = ["https://github.com"]

    request = await UniversalAgent().contextualize_step(event, agent_config=_config(web_fetch=WebFetchConfig()), t=T)

    head = request.history[0].content
    assert "- https://github.com" in head
    assert "fetch_web_pages" in head


@pytest.mark.asyncio
async def test_with_web_fetch_off_the_linked_pages_are_named_as_unreadable():
    """Without the note a model handed a bare URL summarised the page it imagined from it."""
    event = _message(ChatMessage(role=MessageRole.USER, content="Summarize https://example.com/a"))
    event.web_references = ["https://github.com"]

    request = await UniversalAgent().contextualize_step(event, agent_config=_config(), t=T)

    head = request.history[0].content
    assert "- https://example.com/a\n- https://github.com" in head
    assert "cannot open links" in head
    assert "fetch_web_pages" not in head


@pytest.mark.asyncio
async def test_with_web_fetch_off_a_message_without_links_gets_no_note():
    event = _message(ChatMessage(role=MessageRole.USER, content="Hi"))

    request = await UniversalAgent().contextualize_step(event, agent_config=_config(), t=T)

    assert "cannot open links" not in request.history[0].content


@pytest.mark.asyncio
async def test_the_loop_gets_the_messages_files_and_references():
    event = _message(ChatMessage(role=MessageRole.USER, content="Summarise the report and https://example.com/a"))
    event.web_references = ["https://example.com/b"]
    ctx = ConversationContextualizedEvent(history=event.messages, query="Summarise the report")

    request = await UniversalAgent().loop_step(ctx, event)

    assert (request.loop, request.files, request.knowledge_references) == ("tools", [REPORT], [POLICIES])
    assert request.web_references == ["https://example.com/a", "https://example.com/b"]


@pytest.mark.asyncio
async def test_the_reply_completes_the_turn():
    answer = LLMEvent(
        input_messages=[],
        output_messages=[Message.from_string(role="assistant", content="Done.")],
        chat_model_name="text-generation/dummy",
    )
    ctx = ConversationContextualizedEvent(history=[], query="Summarise the report")

    events = await UniversalAgent().complete_step(
        ToolLoopFinishedEvent(answer=answer), ctx, agent_config=_config(), topic=MagicMock(), t=T, user=None
    )

    assert [type(event) for event in events] == [CompleteConversationEvent]


DOCUMENT_TOOLS = {
    "list_knowledge_documents",
    "search_knowledge_content",
    "read_knowledge_document",
    "select_knowledge_documents",
}


def _tool_context(config: UniversalAgentConfig):
    from swiss_ai_hub.core.displayers import EventDisplayer

    from swiss_ai_hub.agent.capabilities.tool_loop.tool_context import ToolContext

    return ToolContext(agent_config=config, displayer=MagicMock(spec=EventDisplayer), t=T)


def test_a_profile_saved_before_the_document_tools_is_offered_none_of_them():
    """The document tools and the extraction stay off until a profile switches them on."""
    from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction import RecordExtraction

    context = _tool_context(_config())

    assert not DOCUMENT_TOOLS & set(UniversalAgent.tools.function_tools(context))
    assert RecordExtraction.tool_definition(context) is None


def test_a_profile_with_the_document_tools_on_offers_them():
    from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_config import KnowledgeDocumentConfig

    context = _tool_context(_config(knowledge_documents=KnowledgeDocumentConfig(enabled=True)))

    assert DOCUMENT_TOOLS <= set(UniversalAgent.tools.function_tools(context))


def test_the_form_never_offers_ranking_by_meaning():
    """Only a blueprint whose prompt leads the model through the ranking offers it; this one's prompt does not."""
    from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_config import KnowledgeDocumentConfig

    form = UniversalAgentConfig.as_form()
    context = _tool_context(_config(knowledge_documents=KnowledgeDocumentConfig(enabled=True)))

    assert form.knowledge_documents.semantic_search is False
    assert "rank_knowledge_documents" not in UniversalAgent.tools.function_tools(context)


@pytest.mark.asyncio
async def test_an_earlier_table_reaches_the_loop_as_one_line():
    from swiss_ai_hub.core.generative_ai import ExtractedTableMarkup

    earlier = f"{ExtractedTableMarkup.wrap('| a |', rows=4)}\n\nSummary"
    event = _message(
        ChatMessage(role=MessageRole.USER, content="first"),
        ChatMessage(role=MessageRole.ASSISTANT, content=earlier),
        ChatMessage(role=MessageRole.USER, content="next"),
    )

    request = await UniversalAgent().contextualize_step(event, agent_config=_config(), t=T)

    assert request.history[2].content == "[A table of 4 extracted rows was shown here.]\n\nSummary"
