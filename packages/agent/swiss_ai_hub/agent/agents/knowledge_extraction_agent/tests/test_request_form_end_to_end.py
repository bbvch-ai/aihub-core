"""
The Knowledge Extraction Agent's request form through the real dispatcher (NATS + Valkey), answered the way the API
answers it, with the documents, object storage and every model call stubbed.

What the step-level tests cannot show: the form pauses the run, the chat client's generic answer is read back as the
agent's own `ExtractionRequestFormResponseEvent` and triggers only the confirm step, and the reading waits in the run
context across the pause. Marked self_hosted: needs the dev stack's NATS and Valkey, nothing else.
"""

from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent import (
    CompleteConversationEvent,
    ExtractRecordsEvent,
    HumanInTheLoopChatResponseEvent,
    HumanInTheLoopResponseEvent,
    NotAMetaQuestionEvent,
    RecordsExtractedEvent,
    StopEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.generative_ai import KnowledgeDocumentListing, KnowledgeDocumentReader, LLMConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.testing import async_test
from swiss_ai_hub.core.testing.auth_utils import fake_user
from swiss_ai_hub.core.topic_managers import AgentTopicManager

from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_answer import ExtractionRequestAnswer
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_form import ExtractionRequestForm
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_form_request_event import (
    ExtractionRequestFormRequestEvent,
)
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_form_response_event import (
    ExtractionRequestFormResponseEvent,
)
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_reading import ExtractionRequestReading
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.knowledge_extraction_agent import KnowledgeExtractionAgent
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.knowledge_extraction_agent_config import (
    KnowledgeExtractionAgentConfig,
)
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_collection import (
    KnowledgeDocumentCollection,
)
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_config import KnowledgeDocumentConfig
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_run_scope import (
    KnowledgeDocumentRunScope,
)
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_scope import KnowledgeDocumentScope
from swiss_ai_hub.agent.capabilities.tests.test_record_extraction_end_to_end import FINANCE, _document, _stub
from swiss_ai_hub.agent.i18n.agent_locale_handler import AgentLocaleHandler
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner

pytestmark = pytest.mark.self_hosted

CONVERSATION_MODULE = "swiss_ai_hub.agent.capabilities.conversation.conversation"
DOCUMENTS = [_document("invoices/2025/a.pdf"), _document("invoices/2025/b.pdf")]
READING = ExtractionRequestAnswer(
    is_table_request=True,
    confirms_sample=False,
    locations=[],
    fields="item, amount",
    instructions="only hardware",
    calculation=None,
    document_kind=None,
    row_terms="Rack",
    document_terms=None,
)


def _config() -> KnowledgeExtractionAgentConfig:
    return KnowledgeExtractionAgentConfig(
        agent_id=f"extraction-{ObjectId()}",
        name=LocaleString(en="Extraction"),
        description=LocaleString(en="Extraction fixture"),
        llm=LLMConfig(model_name="text-generation/dummy"),
        knowledge_documents=KnowledgeDocumentConfig(enabled=True, narrow_references=True),
    )


def _stub_agent(monkeypatch: pytest.MonkeyPatch) -> dict[str, AsyncMock]:
    """The documents, the reading and the conversation's model calls; the mocks count how often each step ran."""
    _stub(monkeypatch, {None: DOCUMENTS})
    reading = AsyncMock(return_value=READING)
    understood = AsyncMock(side_effect=ExtractionRequestForm.understood)
    detect = AsyncMock(return_value=NotAMetaQuestionEvent(reasoning="a table request"))

    async def detect_meta_question(**kwargs: Any) -> NotAMetaQuestionEvent:
        return await detect(**kwargs)

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
    monkeypatch.setattr(
        KnowledgeDocumentReader,
        "list_documents",
        staticmethod(AsyncMock(return_value=KnowledgeDocumentListing.from_summaries(DOCUMENTS))),
    )
    monkeypatch.setattr(ExtractionRequestReading, "ask", staticmethod(reading))
    monkeypatch.setattr(ExtractionRequestForm, "understood", staticmethod(understood))
    return {"contextualize": detect, "discover": reading, "confirm": understood}


def _answer_as_the_api(request: ExtractionRequestFormRequestEvent, text: str) -> HumanInTheLoopResponseEvent:
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
    runner = AgentTestRunner(agent_type=KnowledgeExtractionAgent, agent_config=_config())
    async with runner.test_run(delay_before_stop=30) as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[ChatMessage(role=MessageRole.USER, content="Hardware lines of the 2025 invoices")],
                user=fake_user(),
                locale="en",
            ),
        )
        request = await runner.wait_for_event(ExtractionRequestFormRequestEvent, timeout=20)
        await runner.send_event_from_topic(start_event=_answer_as_the_api(request, text), topic=request.topic)
    return runner


@async_test
async def test_the_form_answer_resumes_the_run_at_the_confirm_step_with_the_reading_kept(monkeypatch):
    steps = _stub_agent(monkeypatch)

    runner = await _run_with_answer('{"where": {"type": "option", "option_index": 0}}')

    assert not runner.has_exception_event
    assert len(_control(runner, ExtractionRequestFormRequestEvent)) == 1
    responses = _control(runner, ExtractionRequestFormResponseEvent)
    assert len(responses) == 1
    assert type(responses[0]) is ExtractionRequestFormResponseEvent
    assert [mock.await_count for mock in steps.values()] == [1, 1, 1]
    extraction = _control(runner, ExtractRecordsEvent)
    assert len(extraction) == 1
    assert (extraction[0].fields, extraction[0].instructions, extraction[0].row_terms) == (
        "item, amount",
        "only hardware",
        "Rack",
    )
    table = _control(runner, RecordsExtractedEvent)
    assert len(table) == 1
    assert table[0].file_count == 2
    assert len(_control(runner, StopEvent)) == 1


@async_test
async def test_a_typed_no_ends_the_run_without_reading_a_document(monkeypatch):
    steps = _stub_agent(monkeypatch)

    runner = await _run_with_answer("no")

    assert not runner.has_exception_event
    assert steps["confirm"].await_count == 0
    assert _control(runner, ExtractRecordsEvent) == []
    completion = _control(runner, CompleteConversationEvent)
    declined = AgentLocaleHandler("en")("agent.knowledge_extraction_agent.messages.declined")
    assert completion[0].answer.output_messages[-1].content == declined
    assert len(_control(runner, StopEvent)) == 1
