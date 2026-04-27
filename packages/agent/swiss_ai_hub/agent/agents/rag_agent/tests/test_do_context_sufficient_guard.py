from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent.guard.context_insufficient_reject_event import ContextInsufficientRejectEvent
from swiss_ai_hub.core.generative_ai.chat_history.extend_chat_history_with_organization_memory import (
    extend_chat_history_with_organization_memory,
)
from swiss_ai_hub.core.generative_ai.guards.context_sufficient_guard import ContextGuardResult
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.infrastructure.mem0.types.memory import Memory
from swiss_ai_hub.core.infrastructure.mem0.types.memory_metadata import MemoryMetadata
from swiss_ai_hub.core.infrastructure.mem0.types.memory_type import MemoryType

from swiss_ai_hub.agent.rag.step_functions import do_context_sufficient_guard


def _build_org_memory(memory_text: str) -> Memory:
    return Memory(
        id="m-1",
        owner_id="user-1",
        memory=memory_text,
        score=0.9,
        created_at="2026-04-23T00:00:00Z",
        metadata=MemoryMetadata(
            user_id="user-1",
            agent_id="rag-agent",
            thread_id="thread-1",
            display_id="display-1",
            run_id="run-1",
            type=MemoryType.ORGANIZATION_MEMORY,
        ),
    )


@pytest.fixture
def locale_handler() -> LocaleHandler:
    return LocaleHandler(locale="en")


@pytest.fixture
def mock_llm() -> MagicMock:
    llm = MagicMock()
    llm.metadata.is_function_calling_model = True
    llm.astructured_predict = AsyncMock(
        return_value=ContextGuardResult(
            reasoning="Memory already provides the answer",
            success=True,
            new_query=None,
        )
    )
    return llm


@pytest.fixture
def llm_config(mock_llm):
    config = MagicMock()

    @asynccontextmanager
    async def ctx(_displayer):
        yield mock_llm

    config.cost_reporting_llm = ctx
    return config


@pytest.fixture
def displayer():
    d = MagicMock()
    d.display_thought = AsyncMock()
    d.display_llm_costs = AsyncMock()
    return d


@pytest.fixture
def run_context():
    ctx = MagicMock()
    ctx.get = AsyncMock(side_effect=lambda key, default=None: default)
    ctx.set = AsyncMock()
    return ctx


@pytest.mark.asyncio
async def test_organization_memory_system_message_reaches_guard_prompt(
    mock_llm, llm_config, displayer, run_context, locale_handler
):
    """End-to-end wiring: extend_chat_history_with_organization_memory injects a system message,
    and do_context_sufficient_guard must forward that chat history into the LLM prompt so the
    guard can accept based on stored memory instead of requiring fresh retrieval."""
    memory_text = "Vacation policy allows 25 days per year."
    chat_history_with_memory = extend_chat_history_with_organization_memory(
        chat_history=[
            ChatMessage(role=MessageRole.USER, content="What is our vacation policy?"),
        ],
        memories=[_build_org_memory(memory_text)],
        relations=None,
        t=locale_handler,
    )

    await do_context_sufficient_guard(
        user_query="What is our vacation policy?",
        context="Employee handbook chapter 3.",
        check_context_sufficiency=True,
        max_hops=3,
        run_context=run_context,
        llm_config=llm_config,
        displayer=displayer,
        t=locale_handler,
        chat_history=chat_history_with_memory,
    )

    rendered_chat_history = mock_llm.astructured_predict.call_args.kwargs["chat_history"]
    assert memory_text in rendered_chat_history
    assert "user:" in rendered_chat_history
    assert "What is our vacation policy?" in rendered_chat_history


@pytest.mark.asyncio
async def test_guard_forwards_full_chat_history_including_user_and_assistant_turns(
    mock_llm, llm_config, displayer, run_context, locale_handler
):
    chat_history = [
        ChatMessage(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
        ChatMessage(role=MessageRole.SYSTEM, content="Memory: 25 vacation days."),
        ChatMessage(role=MessageRole.USER, content="First question"),
        ChatMessage(role=MessageRole.ASSISTANT, content="Earlier answer"),
        ChatMessage(role=MessageRole.USER, content="Follow-up"),
    ]

    await do_context_sufficient_guard(
        user_query="Follow-up",
        context="Some context.",
        check_context_sufficiency=True,
        max_hops=3,
        run_context=run_context,
        llm_config=llm_config,
        displayer=displayer,
        t=locale_handler,
        chat_history=chat_history,
    )

    rendered = mock_llm.astructured_predict.call_args.kwargs["chat_history"]
    assert "Memory: 25 vacation days." in rendered
    assert "First question" in rendered
    assert "Earlier answer" in rendered
    assert "Follow-up" in rendered


@pytest.mark.asyncio
async def test_guard_with_empty_chat_history_still_renders_empty_placeholder(
    mock_llm, llm_config, displayer, run_context, locale_handler
):
    await do_context_sufficient_guard(
        user_query="What is the capital of France?",
        context="Paris is the capital of France.",
        check_context_sufficiency=True,
        max_hops=3,
        run_context=run_context,
        llm_config=llm_config,
        displayer=displayer,
        t=locale_handler,
        chat_history=[],
    )

    assert mock_llm.astructured_predict.call_args.kwargs["chat_history"] == ""


@pytest.mark.asyncio
async def test_guard_sets_context_sufficient_false_when_no_more_hops(
    mock_llm, llm_config, displayer, run_context, locale_handler
):
    mock_llm.astructured_predict = AsyncMock(
        return_value=ContextGuardResult(
            reasoning="Context does not answer the question",
            success=False,
            new_query=None,
        )
    )

    result = await do_context_sufficient_guard(
        user_query="What is the meaning of life?",
        context="Unrelated document.",
        check_context_sufficiency=True,
        max_hops=1,
        run_context=run_context,
        llm_config=llm_config,
        displayer=displayer,
        t=locale_handler,
        chat_history=[],
    )

    assert isinstance(result, ContextInsufficientRejectEvent)
    run_context.set.assert_any_await("context_sufficient", False)


@pytest.mark.asyncio
async def test_guard_does_not_write_context_sufficient_on_accept(
    mock_llm, llm_config, displayer, run_context, locale_handler
):
    await do_context_sufficient_guard(
        user_query="What is the capital of France?",
        context="Paris is the capital of France.",
        check_context_sufficiency=True,
        max_hops=3,
        run_context=run_context,
        llm_config=llm_config,
        displayer=displayer,
        t=locale_handler,
        chat_history=[],
    )

    written_keys = [call.args[0] for call in run_context.set.await_args_list]
    assert "context_sufficient" not in written_keys
