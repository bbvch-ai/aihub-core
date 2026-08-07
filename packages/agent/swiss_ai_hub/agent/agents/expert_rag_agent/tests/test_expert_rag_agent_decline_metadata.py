"""
Unit coverage for the expert-decline and expert-error exit paths: both bypass ExpertRAGAgent's normal
metadata call site (stop_step), the same "dispatcher won't dispatch a step waiting on a stop event"
reason as the meta-question branch. Title already fires early (fan-out step, unaffected); only
follow-ups were missing here.

Calls the step methods directly (same style as conversation_metadata/tests/test_conversation_metadata_
step_functions.py's direct calls to the shared free functions) rather than driving the full dispatcher —
these paths need an AgentInTheLoop round-trip to reach through the real dispatcher, which is a much
heavier integration surface for no added coverage of the metadata wiring itself.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.agents import AgentRef
from swiss_ai_hub.core.events.agent import AgentInTheLoop, ExceptionEvent, StopEvent, UserMessageEvent
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.testing.auth_utils import fake_user

from swiss_ai_hub.agent.agents.expert_rag_agent.configs.expert_rag_agent_config import ExpertRAGAgentConfig
from swiss_ai_hub.agent.agents.expert_rag_agent.expert_rag_agent import ExpertRAGAgent
from swiss_ai_hub.agent.agents.rag_agent.configs.expert_escalation_config import ExpertEscalationConfig
from swiss_ai_hub.agent.i18n.agent_locale_handler import AgentLocaleHandler
from swiss_ai_hub.agent.steps.guards.context_sufficient_guard_step.context_sufficient_guard_step_config import (
    ContextSufficientGuardStepConfig,
)

EXPERT_RAG_MODULE = "swiss_ai_hub.agent.agents.expert_rag_agent.expert_rag_agent"


def _config() -> ExpertRAGAgentConfig:
    return ExpertRAGAgentConfig(
        agent_id="expert_decline_metadata_test",
        name=LocaleString(en="Test Expert RAG"),
        description=LocaleString(en="A test expert RAG agent."),
        llm=LLMConfig(model_name="text-generation/dummy"),
        retrievers=[],
        number_of_input_tokens=8192,
        context_sufficient_guard=ContextSufficientGuardStepConfig(check_context_sufficiency=False),
        expert_escalation=ExpertEscalationConfig(agent=AgentRef(agent_class="ExpertAskingAgent", agent_id="expert")),
    )


def _user_message() -> UserMessageEvent:
    return UserMessageEvent(
        messages=[ChatMessage(content="What is quantum entanglement?", role=MessageRole.USER)],
        user=fake_user(),
        locale="en",
    )


@pytest.fixture
def displayer() -> MagicMock:
    d = MagicMock()
    d.display_thought = AsyncMock()
    d.display_chunk = AsyncMock()
    return d


@pytest.mark.asyncio
async def test_expert_not_answered_generates_follow_ups(monkeypatch, displayer):
    recorded = {}

    async def fake_generate_follow_ups(chat_messages, llm_config, disp, t):
        recorded["chat_messages"] = chat_messages

    monkeypatch.setattr(f"{EXPERT_RAG_MODULE}.generate_follow_up_questions", fake_generate_follow_ups)

    agent = ExpertRAGAgent()
    result = await agent.expert_not_answered_step(
        displayer=displayer,
        _=AgentInTheLoop.response(stop_event=StopEvent()),
        user_message_event=_user_message(),
        agent_config=_config(),
        t=AgentLocaleHandler("en"),
    )

    assert result.reason == "expert_declined"
    assert "chat_messages" in recorded, "expert_not_answered_step must call generate_follow_up_questions"
    roles = [m.role for m in recorded["chat_messages"]]
    assert roles == [MessageRole.USER, MessageRole.ASSISTANT], (
        "follow-ups must be grounded on the original question plus the canned decline message"
    )


@pytest.mark.asyncio
async def test_expert_exception_generates_follow_ups(monkeypatch, displayer):
    recorded = {}

    async def fake_generate_follow_ups(chat_messages, llm_config, disp, t):
        recorded["chat_messages"] = chat_messages

    monkeypatch.setattr(f"{EXPERT_RAG_MODULE}.generate_follow_up_questions", fake_generate_follow_ups)

    agent = ExpertRAGAgent()
    exception_event = AgentInTheLoop.exception(exception_event=ExceptionEvent(message="boom", http_status_code=500))
    result = await agent.expert_exception_step(
        displayer=displayer,
        exception_event=exception_event,
        user_message_event=_user_message(),
        agent_config=_config(),
        t=AgentLocaleHandler("en"),
    )

    assert result.reason == "expert_errored"
    assert "chat_messages" in recorded, "expert_exception_step must call generate_follow_up_questions"
    roles = [m.role for m in recorded["chat_messages"]]
    assert roles == [MessageRole.USER, MessageRole.ASSISTANT]
