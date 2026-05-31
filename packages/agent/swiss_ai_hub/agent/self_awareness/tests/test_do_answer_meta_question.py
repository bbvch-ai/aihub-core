from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent import LLMStopEvent, MetaQuestionDetectedEvent

from swiss_ai_hub.agent.i18n.agent_locale_handler import AgentLocaleHandler
from swiss_ai_hub.agent.self_awareness.self_awareness_step_functions import do_answer_meta_question


@pytest.fixture
def locale_handler() -> AgentLocaleHandler:
    return AgentLocaleHandler("en")


@pytest.fixture
def llm_config() -> MagicMock:
    config = MagicMock()

    @asynccontextmanager
    async def ctx(_displayer):
        yield MagicMock()

    config.cost_reporting_llm = ctx
    return config


@pytest.fixture
def displayer() -> MagicMock:
    d = MagicMock()
    d.display_thought = AsyncMock()
    d.display_llm_stream = AsyncMock(return_value=LLMStopEvent(chat_messages=[]))
    return d


@pytest.mark.asyncio
async def test_answer_prompt_is_grounded_in_agent_identity_and_workflow(llm_config, displayer, locale_handler):
    event = MetaQuestionDetectedEvent(
        user_query="What can you do?", category="capabilities", reasoning="asks about abilities"
    )

    result = await do_answer_meta_question(
        event=event,
        agent_name="HR Assistant",
        agent_description="Answers HR policy questions.",
        workflow_summary="- Retrieve documents\n- Generate an answer",
        chat_history=[ChatMessage(role=MessageRole.USER, content="What can you do?")],
        llm_config=llm_config,
        displayer=displayer,
        t=locale_handler,
    )

    assert isinstance(result, LLMStopEvent)
    displayer.display_thought.assert_awaited_once()

    # The system prompt the LLM received must be grounded in THIS agent's identity + workflow.
    sent_messages = displayer.display_llm_stream.call_args.args[2]
    system_text = "\n".join(m.content for m in sent_messages if m.role == MessageRole.SYSTEM)
    assert "HR Assistant" in system_text
    assert "Answers HR policy questions." in system_text
    assert "Retrieve documents" in system_text
    assert "Generate an answer" in system_text


@pytest.mark.asyncio
async def test_answer_terminates_as_stop_step(llm_config, displayer, locale_handler):
    event = MetaQuestionDetectedEvent(user_query="who are you?", category="identity", reasoning="identity")

    await do_answer_meta_question(
        event=event,
        agent_name="Bot",
        agent_description="A bot.",
        workflow_summary="- Answer",
        chat_history=[],
        llm_config=llm_config,
        displayer=displayer,
        t=locale_handler,
    )

    assert displayer.display_llm_stream.call_args.kwargs["as_stop_step"] is True
