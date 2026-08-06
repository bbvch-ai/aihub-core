"""
Integration guard for the meta-question gate: drives RAGAgent through the real dispatcher
(NATS + Redis) with detection/answer forced, and proves a meta question never reaches retrieval.

Needs the dev stack (NATS + Valkey) but no LLM or Milvus — detection and answer are stubbed,
and the meta branch stops before any retriever runs. Marked self_hosted so the lean CI skips it;
the deterministic wiring is covered infra-free in test_meta_question_gate.py.
"""

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent import (
    ConversationTitleEvent,
    FollowUpQuestionsEvent,
    LLMStopEvent,
    MetaQuestionDetectedEvent,
    NotAMetaQuestionEvent,
    RetrieveOrganizationMemoryEvent,
    RetrieverEvent,
    RetrieveUserMemoryEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.testing import async_test
from swiss_ai_hub.core.testing.auth_utils import fake_user

from swiss_ai_hub.agent.agents.rag_agent.configs.rag_agent_config import RAGAgentConfig
from swiss_ai_hub.agent.agents.rag_agent.rag_agent import RAGAgent
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner
from swiss_ai_hub.agent.steps.guards.context_sufficient_guard_step.context_sufficient_guard_step_config import (
    ContextSufficientGuardStepConfig,
)

pytestmark = pytest.mark.self_hosted

RAG_MODULE = "swiss_ai_hub.agent.agents.rag_agent.rag_agent"


def _config() -> RAGAgentConfig:
    return RAGAgentConfig(
        agent_id="meta_routing_rag",
        name=LocaleString(en="Test RAG"),
        description=LocaleString(en="A test RAG agent."),
        llm=LLMConfig(model_name="text-generation/dummy"),
        retrievers=[],
        number_of_input_tokens=8192,
        context_sufficient_guard=ContextSufficientGuardStepConfig(check_context_sufficiency=False),
    )


def _user_message(text: str) -> UserMessageEvent:
    return UserMessageEvent(
        messages=[ChatMessage(content=text, role=MessageRole.USER)],
        user=fake_user(),
        locale="en",
    )


@async_test
async def test_meta_question_answers_without_retrieval(monkeypatch):
    async def fake_detect(*, user_query, **_):
        return MetaQuestionDetectedEvent(user_query=user_query, category="capabilities", reasoning="forced meta")

    async def fake_answer(**_):
        answer = ChatMessage(role=MessageRole.ASSISTANT, content="I can answer HR questions.")
        return LLMStopEvent(chat_messages=[answer])

    # generate_title/generate_follow_up_questions are stubbed too, same as detection/answer — this test
    # stays LLM-free per its docstring. Each fake emits the real event so the assertions below prove the
    # meta branch actually WIRES the generators in, not just that stubbed functions were called.
    async def fake_generate_title(*_args, **_kwargs):
        pass

    async def fake_generate_follow_ups(*_args, **_kwargs):
        pass

    monkeypatch.setattr(f"{RAG_MODULE}.do_detect_meta_question", fake_detect)
    monkeypatch.setattr(f"{RAG_MODULE}.do_answer_meta_question", fake_answer)
    monkeypatch.setattr(f"{RAG_MODULE}.generate_title", fake_generate_title)
    monkeypatch.setattr(f"{RAG_MODULE}.generate_follow_up_questions", fake_generate_follow_ups)

    runner = AgentTestRunner(agent_type=RAGAgent, agent_config=_config())
    async with runner.test_run(delay_before_stop=30) as topic:
        await runner.send_event_from_topic(topic=topic, start_event=_user_message("What can you do?"))

    assert runner.has_event_of_class(MetaQuestionDetectedEvent), "detection did not route to the meta branch"
    assert runner.has_stop_event, "meta branch did not terminate the run"
    # The race-condition guard: the gate must hold the pipeline back entirely.
    assert not runner.has_event_of_class(RetrieverEvent), "retrieval ran for a meta question — gate failed"
    assert not runner.has_event_of_class(RetrieveUserMemoryEvent)
    assert not runner.has_event_of_class(RetrieveOrganizationMemoryEvent)
    assert not runner.has_exception_event


@async_test
async def test_meta_question_branch_generates_title_and_follow_ups(monkeypatch):
    """The meta branch now generates conversation metadata too (previously left as-is, per ADR
    2026_06_18) — title in parallel with the answer, follow-ups grounded on it."""

    async def fake_detect(*, user_query, **_):
        return MetaQuestionDetectedEvent(user_query=user_query, category="identity", reasoning="forced meta")

    async def fake_answer(**_):
        answer = ChatMessage(role=MessageRole.ASSISTANT, content="I am the HR assistant.")
        return LLMStopEvent(chat_messages=[answer])

    async def fake_generate_title(chat_messages, llm_config, displayer, t, thread_context):
        await displayer.display_event(ConversationTitleEvent(title="Fake Title"))

    async def fake_generate_follow_ups(chat_messages, llm_config, displayer, t):
        await displayer.display_event(FollowUpQuestionsEvent(questions=["Fake follow-up?"]))

    monkeypatch.setattr(f"{RAG_MODULE}.do_detect_meta_question", fake_detect)
    monkeypatch.setattr(f"{RAG_MODULE}.do_answer_meta_question", fake_answer)
    monkeypatch.setattr(f"{RAG_MODULE}.generate_title", fake_generate_title)
    monkeypatch.setattr(f"{RAG_MODULE}.generate_follow_up_questions", fake_generate_follow_ups)

    runner = AgentTestRunner(agent_type=RAGAgent, agent_config=_config())
    async with runner.test_run(delay_before_stop=30) as topic:
        await runner.send_event_from_topic(topic=topic, start_event=_user_message("who are you?"))

    assert runner.has_event_of_class(MetaQuestionDetectedEvent)
    assert runner.has_event_of_class(ConversationTitleEvent), "meta branch did not generate a title"
    assert runner.has_event_of_class(FollowUpQuestionsEvent), "meta branch did not generate follow-ups"
    assert not runner.has_exception_event


@async_test
async def test_normal_question_opens_the_gate(monkeypatch):
    """When detection clears the message, the normal entry steps are released (gate opens)."""

    async def fake_detect(*, user_query, llm_config, displayer, t, user):
        return NotAMetaQuestionEvent(reasoning="normal task")

    monkeypatch.setattr(f"{RAG_MODULE}.do_detect_meta_question", fake_detect)

    runner = AgentTestRunner(agent_type=RAGAgent, agent_config=_config())
    async with runner.test_run(delay_before_stop=20) as topic:
        await runner.send_event_from_topic(topic=topic, start_event=_user_message("What is the vacation policy?"))

    assert runner.has_event_of_class(NotAMetaQuestionEvent)
    # The gate opened: the condense step (first step past the gated entry steps) ran.
    from swiss_ai_hub.core.events.agent import LimitChatHistoryEvent

    assert runner.has_event_of_class(LimitChatHistoryEvent), "gate did not release the normal pipeline"
    assert not runner.has_event_of_class(MetaQuestionDetectedEvent)
