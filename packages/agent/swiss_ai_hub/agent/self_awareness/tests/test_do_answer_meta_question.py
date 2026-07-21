from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from openai import BadRequestError
from swiss_ai_hub.core.events.agent import LLMStopEvent, MetaQuestionDetectedEvent

from swiss_ai_hub.agent.i18n.agent_locale_handler import AgentLocaleHandler
from swiss_ai_hub.agent.self_awareness.self_awareness_step_functions import do_answer_meta_question


@pytest.fixture
def locale_handler() -> AgentLocaleHandler:
    return AgentLocaleHandler("en")


@pytest.fixture
def llm() -> SimpleNamespace:
    """A minimal stand-in exposing the mutable ``additional_kwargs`` the reasoning-off path writes to."""
    return SimpleNamespace(additional_kwargs={})


@pytest.fixture
def llm_config(llm) -> MagicMock:
    config = MagicMock()

    @asynccontextmanager
    async def ctx(_displayer):
        yield llm

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
async def test_answer_drops_empty_history_turns(llm_config, displayer, locale_handler):
    """A prior meta answer captured empty by the chat client must not reach the LLM (providers 400 on
    an empty assistant message), which would blank out this follow-up answer."""
    event = MetaQuestionDetectedEvent(user_query="why did you do that?", category="behavior", reasoning="behavior")

    await do_answer_meta_question(
        event=event,
        agent_name="Bot",
        agent_description="A bot.",
        workflow_summary="- Answer",
        chat_history=[
            ChatMessage(role=MessageRole.USER, content="what can you do?"),
            ChatMessage(role=MessageRole.ASSISTANT, content=""),
            ChatMessage(role=MessageRole.USER, content="why did you do that?"),
        ],
        llm_config=llm_config,
        displayer=displayer,
        t=locale_handler,
    )

    sent_messages = displayer.display_llm_stream.call_args.args[2]
    assert all(str(m.content or "").strip() for m in sent_messages), "empty-content turns must be dropped"


@pytest.mark.asyncio
async def test_answer_disables_reasoning_on_the_streamed_response(llm, llm_config, displayer, locale_handler):
    """A meta answer needs no chain-of-thought; reasoning is pure latency, so it must be turned off. The
    streaming path takes no per-call kwargs, so the flag is baked onto the LLM instance before streaming."""
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

    assert llm.additional_kwargs["extra_body"]["chat_template_kwargs"] == {"thinking": False, "enable_thinking": False}


@pytest.mark.asyncio
async def test_answer_falls_back_to_plain_stream_when_reasoning_flag_rejected(
    llm, llm_config, displayer, locale_handler
):
    """Mistral-tokenizer models reject chat_template_kwargs with a 400 before any chunk streams; the answer
    must retry as a plain request rather than fail the run."""
    displayer.display_llm_stream = AsyncMock(
        side_effect=[
            BadRequestError("chat_template not supported", response=MagicMock(status_code=400), body=None),
            LLMStopEvent(chat_messages=[]),
        ]
    )
    event = MetaQuestionDetectedEvent(user_query="who are you?", category="identity", reasoning="identity")

    result = await do_answer_meta_question(
        event=event,
        agent_name="Bot",
        agent_description="A bot.",
        workflow_summary="- Answer",
        chat_history=[],
        llm_config=llm_config,
        displayer=displayer,
        t=locale_handler,
    )

    assert isinstance(result, LLMStopEvent)
    assert displayer.display_llm_stream.await_count == 2
    assert "extra_body" not in llm.additional_kwargs, "the retry must send a plain request"


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
