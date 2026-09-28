"""
Drives a spine blueprint through the real dispatcher (NATS + Valkey) with every model call stubbed.

What this proves that the infra-free tests cannot: the dispatcher calls a contributed static step with the
blueprint instance in first position, injects the concrete config into a parameter annotated with a capability's
config base, injects `type[Agent]` into the spine's preconditions, fans the list results of the enrichers out as
separate events, and the two barriers (context blocks, post-answer hooks) release exactly once.
Marked self_hosted: needs the dev stack's NATS and Valkey, nothing else.
"""

from contextlib import asynccontextmanager
from unittest.mock import MagicMock

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    AnswerPostProcessedEvent,
    ContextBlockEvent,
    ConversationQueryEvent,
    EnrichedChatHistoryEvent,
    LimitChatHistoryEvent,
    LLMEvent,
    LLMStopEvent,
    Message,
    NotAMetaQuestionEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.testing import async_test
from swiss_ai_hub.core.testing.auth_utils import fake_user
from swiss_ai_hub.core.topic_managers import AgentTopicManager

from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent import LLMWrappingAgent
from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent_config import LLMWrappingAgentConfig
from swiss_ai_hub.agent.capabilities.memory.user_memory_config import UserMemoryConfig
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner

pytestmark = pytest.mark.self_hosted

SPINE_MODULE = "swiss_ai_hub.agent.capabilities.conversation.conversation_capability"
SELF_AWARENESS_MODULE = "swiss_ai_hub.agent.capabilities.self_awareness.self_awareness_capability"


def _config() -> LLMWrappingAgentConfig:
    return LLMWrappingAgentConfig(
        agent_id="spine_end_to_end",
        name=LocaleString(en="Spine"),
        description=LocaleString(en="Spine end-to-end fixture"),
        system_prompt=LocaleString(en="You are helpful."),
        llm=LLMConfig(model_name="text-generation/dummy"),
        number_of_input_tokens=8192,
        user_memory=UserMemoryConfig(enable_user_memory_retrieval=False, enable_user_memory_storage=False),
        org_memory=None,
    )


@async_test
async def test_a_turn_runs_the_whole_spine_through_the_dispatcher(monkeypatch):
    async def fake_detect(*, user_query, **_):
        return NotAMetaQuestionEvent(reasoning="normal task")

    async def fake_stream(self, llm_config, llm, messages, as_stop_step=True):
        return LLMEvent(output_messages=[Message.from_string(role="assistant", content="25 days")])

    @asynccontextmanager
    async def fake_cost_reporting(self, displayer, user=None):
        yield MagicMock()

    async def no_metadata(*_args, **_kwargs):
        pass

    monkeypatch.setattr(f"{SELF_AWARENESS_MODULE}.do_detect_meta_question", fake_detect)
    monkeypatch.setattr(f"{SPINE_MODULE}.generate_title", no_metadata)
    monkeypatch.setattr(f"{SPINE_MODULE}.generate_follow_up_questions", no_metadata)
    monkeypatch.setattr(EventDisplayer, "display_llm_stream", fake_stream)
    monkeypatch.setattr(LLMConfig, "cost_reporting_llm", fake_cost_reporting)
    monkeypatch.setattr(LLMConfig, "get_model_info", lambda self: {"model_info": {}})

    runner = AgentTestRunner(agent_type=LLMWrappingAgent, agent_config=_config())
    async with runner.test_run(delay_before_stop=20) as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[ChatMessage(content="How many vacation days do I get?", role=MessageRole.USER)],
                user=fake_user(),
                locale="en",
            ),
        )

    assert not runner.has_exception_event
    for event_class in (
        NotAMetaQuestionEvent,
        LimitChatHistoryEvent,
        ConversationQueryEvent,
        EnrichedChatHistoryEvent,
        LLMEvent,
        AnswerPostProcessedEvent,
        LLMStopEvent,
    ):
        assert runner.has_event_of_class(event_class), f"{event_class.__name__} never happened"

    blocks = _control_events(runner, ContextBlockEvent)
    assert {block.source for block in blocks} == {"user_memory", "organization_memory"}
    assert all(block.is_empty for block in blocks)
    assert len(_control_events(runner, EnrichedChatHistoryEvent)) == 1
    assert len(_control_events(runner, LLMStopEvent)) == 1, "the stop barrier must release exactly once"


def _control_events(runner: AgentTestRunner, event_class: type) -> list:
    """The observer sees a control-and-display event once per subject; the control copy is the one that counts."""
    return [
        observed.event
        for observed in runner.observed_events
        if isinstance(observed.event, event_class) and observed.topic.event_type == AgentTopicManager.CONTROL_EVENT
    ]
