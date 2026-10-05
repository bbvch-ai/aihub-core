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


def test_the_blueprint_offers_knowledge_files_memory_and_the_sandbox_in_one_loop():
    UniversalAgent.validate_workflow(UniversalAgentConfig)

    assert {capability.__name__ for capability in UniversalAgent.installed_capabilities()} == {
        "Conversation",
        "ToolLoop",
        "Knowledge",
        "AttachedFiles",
        "Memory",
    }
    assert UniversalAgent.tools.names() == [
        "search_knowledge",
        "read_attached_files",
        "recall_memory",
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
async def test_the_loop_gets_the_messages_files_and_references():
    event = _message(ChatMessage(role=MessageRole.USER, content="Summarise the report"))
    ctx = ConversationContextualizedEvent(history=event.messages, query="Summarise the report")

    request = await UniversalAgent().loop_step(ctx, event)

    assert (request.loop, request.files, request.knowledge_references) == ("tools", [REPORT], [POLICIES])


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
