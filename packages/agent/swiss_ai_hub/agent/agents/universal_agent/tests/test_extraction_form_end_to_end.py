"""
The Universal Agent's request form on `extract_records` through the real dispatcher (NATS + Valkey), inside the tool
loop, answered the way the API answers it, with the documents, object storage and every model call stubbed.

What the step-level tests cannot show: the form pauses the loop in the middle of a round, the chat client's generic
answer is read back as the capability's own `ExtractionCallFormResponseEvent`, and both a confirmation and a decline
answer the call, so the loop's join completes and the model answers. Marked self_hosted: needs the dev stack's NATS and
Valkey, nothing else.
"""

import json
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent import (
    CompleteConversationEvent,
    HumanInTheLoopChatResponseEvent,
    HumanInTheLoopResponseEvent,
    LLMEvent,
    Message,
    NotAMetaQuestionEvent,
    RecordsExtractedEvent,
    StopEvent,
    ToolLoopFinishedEvent,
    ToolResultEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.generative_ai import KnowledgeDocumentListing, KnowledgeDocumentReader, LLMConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.testing import async_test
from swiss_ai_hub.core.testing.auth_utils import fake_user
from swiss_ai_hub.core.topic_managers import AgentTopicManager

from swiss_ai_hub.agent.agents.memory_writer_agent.configs.memory_writer_agent_config import MemoryWriterAgentConfig
from swiss_ai_hub.agent.agents.universal_agent.universal_agent import UniversalAgent
from swiss_ai_hub.agent.agents.universal_agent.universal_agent_config import UniversalAgentConfig
from swiss_ai_hub.agent.capabilities.knowledge.knowledge_tool_scope import KnowledgeToolScope
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_collection import (
    KnowledgeDocumentCollection,
)
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_config import KnowledgeDocumentConfig
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_run_scope import (
    KnowledgeDocumentRunScope,
)
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_scope import KnowledgeDocumentScope
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_call_form_request_event import (
    ExtractionCallFormRequestEvent,
)
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_call_form_response_event import (
    ExtractionCallFormResponseEvent,
)
from swiss_ai_hub.agent.capabilities.tests.test_record_extraction_end_to_end import FINANCE, _document, _stub
from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop import ToolLoop
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner

pytestmark = pytest.mark.self_hosted

CONVERSATION_MODULE = "swiss_ai_hub.agent.capabilities.conversation.conversation"
DOCUMENTS = [_document("invoices/2025/a.pdf"), _document("invoices/2024/b.pdf")]
CALL = {"any_of": [{"content_query": "ACME AG"}], "fields": "item, amount"}
REPLY = "Here is what the extraction returned."


def _config() -> UniversalAgentConfig:
    return UniversalAgentConfig(
        agent_id=f"universal-{ObjectId()}",
        name=LocaleString(en="Universal"),
        description=LocaleString(en="Universal fixture"),
        llm=LLMConfig(model_name="text-generation/dummy"),
        knowledge_documents=KnowledgeDocumentConfig(enabled=True),
    )


async def _scripted_turn(messages: list[ChatMessage], tools: list[dict] | None, *_args: Any) -> LLMEvent:
    """The model calls `extract_records` once, then answers once the call has its result."""
    answered = any(message.role == MessageRole.TOOL for message in messages)
    if answered or not tools:
        return LLMEvent(output_messages=[Message.from_string(role="assistant", content=REPLY)])
    call = {"id": "call-1", "type": "function", "function": {"name": "extract_records", "arguments": json.dumps(CALL)}}
    return LLMEvent(output_messages=[Message(role="assistant", content="", tool_calls=[call])])


def _stub_agent(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    _stub(monkeypatch, {"ACME AG": DOCUMENTS[:1], "**": DOCUMENTS})
    turn = AsyncMock(side_effect=_scripted_turn)

    async def detect_meta_question(**_kwargs: Any) -> NotAMetaQuestionEvent:
        return NotAMetaQuestionEvent(reasoning="a table request")

    async def no_metadata(*_args: Any, **_kwargs: Any) -> None:
        pass

    @asynccontextmanager
    async def cost_reporting(self, displayer, user=None):
        yield MagicMock()

    scope = KnowledgeDocumentRunScope(
        collections=[KnowledgeDocumentCollection(identifier="finance/invoices", collection=FINANCE, label="Finance")]
    )
    monkeypatch.setattr(f"{CONVERSATION_MODULE}.do_detect_meta_question", detect_meta_question)
    monkeypatch.setattr(f"{CONVERSATION_MODULE}.generate_title", no_metadata)
    monkeypatch.setattr(f"{CONVERSATION_MODULE}.generate_follow_up_questions", no_metadata)
    monkeypatch.setattr(LLMConfig, "cost_reporting_llm", cost_reporting)
    monkeypatch.setattr(LLMConfig, "get_model_info", lambda self: {"model_info": {}})
    monkeypatch.setattr(KnowledgeDocumentScope, "of", staticmethod(lambda *_args: scope))
    monkeypatch.setattr(KnowledgeToolScope, "collections", staticmethod(lambda *_args: []))
    monkeypatch.setattr(
        KnowledgeDocumentReader,
        "list_documents",
        staticmethod(AsyncMock(return_value=KnowledgeDocumentListing.from_summaries(DOCUMENTS))),
    )
    monkeypatch.setattr(ToolLoop, "_turn", staticmethod(turn))
    return turn


def _answer_as_the_api(request: ExtractionCallFormRequestEvent, text: str) -> HumanInTheLoopResponseEvent:
    """The answer exactly as `ChatService` builds it: the generic chat response named after the request's topic."""
    topic = request.topic
    return HumanInTheLoopResponseEvent.deserialize_event(
        {
            "_event_name": topic.event_name,
            "_parent_event_names": [topic.event_name, *HumanInTheLoopChatResponseEvent.parent_event_names_from_class()],
            "response": text,
            "request_event": request.model_dump(),
        }
    )


def _control(runner: AgentTestRunner, event_class: type) -> list:
    return [
        observed.event
        for observed in runner.observed_events
        if isinstance(observed.event, event_class) and observed.topic.event_type == AgentTopicManager.CONTROL_EVENT
    ]


async def _run_with_answer(text: str) -> AgentTestRunner:
    runner = AgentTestRunner(agent_type=UniversalAgent, agent_config=_config())
    async with runner.test_run(delay_before_stop=30) as topic:
        await runner.ensure_dependent_agent_stream(MemoryWriterAgentConfig.AGENT_CLASS)
        await runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[ChatMessage(role=MessageRole.USER, content="Items on the ACME AG invoices, as a table")],
                user=fake_user(),
                locale="en",
            ),
        )
        request = await runner.wait_for_event(ExtractionCallFormRequestEvent, timeout=20)
        await runner.send_event_from_topic(start_event=_answer_as_the_api(request, text), topic=request.topic)
    return runner


def _answers_the_call_and_completes(runner: AgentTestRunner, turn: AsyncMock) -> ToolResultEvent:
    assert not runner.has_exception_event
    responses = _control(runner, ExtractionCallFormResponseEvent)
    assert len(responses) == 1
    assert type(responses[0]) is ExtractionCallFormResponseEvent
    results = [result for result in _control(runner, ToolResultEvent) if result.tool_call_id == "call-1"]
    assert len(results) == 1
    assert turn.await_count == 2
    finished = _control(runner, ToolLoopFinishedEvent)
    assert len(finished) == 1
    assert finished[0].answer.output_messages[-1].content == REPLY
    assert len(_control(runner, CompleteConversationEvent)) == 1
    assert len(_control(runner, StopEvent)) == 1
    return results[0]


@async_test
async def test_a_confirmed_form_extracts_and_the_loop_answers(monkeypatch):
    turn = _stub_agent(monkeypatch)

    runner = await _run_with_answer(
        json.dumps({key: {"type": "option", "option_index": 0} for key in ("where", "rows", "columns")})
    )

    result = _answers_the_call_and_completes(runner, turn)
    tables = _control(runner, RecordsExtractedEvent)
    assert len(tables) == 1
    assert tables[0].file_count == 1
    assert not result.is_error


@async_test
async def test_a_declined_form_extracts_nothing_and_the_loop_answers(monkeypatch):
    turn = _stub_agent(monkeypatch)

    runner = await _run_with_answer("no")

    result = _answers_the_call_and_completes(runner, turn)
    assert _control(runner, RecordsExtractedEvent) == []
    assert "declined this extraction" in result.content
