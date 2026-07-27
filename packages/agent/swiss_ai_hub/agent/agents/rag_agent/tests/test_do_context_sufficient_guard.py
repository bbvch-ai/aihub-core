from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest
from llama_index.core.base.llms.types import ChatMessage, ChatResponse, ImageBlock, MessageRole, TextBlock
from swiss_ai_hub.core.events.agent import ContextInsufficientRejectEvent
from swiss_ai_hub.core.generative_ai.chat_history.extend_chat_history_with_organization_memory import (
    extend_chat_history_with_organization_memory,
)
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


def _verdict_response(text: str) -> ChatResponse:
    return ChatResponse(message=ChatMessage(role=MessageRole.ASSISTANT, content=text))


def _prompt_messages(mock_llm: MagicMock) -> list[ChatMessage]:
    """The message list the guard sent to the model (now a plain-text verdict call, not structured)."""
    return mock_llm.achat.call_args.args[0]


def _rendered_text(mock_llm: MagicMock) -> str:
    return " ".join(
        block.text for message in _prompt_messages(mock_llm) for block in message.blocks if isinstance(block, TextBlock)
    )


def _rendered_blocks(mock_llm: MagicMock) -> list:
    return [block for message in _prompt_messages(mock_llm) for block in message.blocks]


@pytest.fixture
def locale_handler() -> LocaleHandler:
    return LocaleHandler(locale="en")


@pytest.fixture
def mock_llm() -> MagicMock:
    llm = MagicMock()
    llm.achat = AsyncMock(return_value=_verdict_response("SUFFICIENT Memory already provides the answer"))
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
    and do_context_sufficient_guard must render that chat history into the guard prompt so the
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
        context_message=ChatMessage(role=MessageRole.USER, blocks=[TextBlock(text="Employee handbook chapter 3.")]),
        check_context_sufficiency=True,
        max_hops=3,
        run_context=run_context,
        llm_config=llm_config,
        displayer=displayer,
        t=locale_handler,
        chat_history=chat_history_with_memory,
    )

    assert memory_text in _rendered_text(mock_llm)


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
        context_message=ChatMessage(role=MessageRole.USER, blocks=[TextBlock(text="Some context.")]),
        check_context_sufficiency=True,
        max_hops=3,
        run_context=run_context,
        llm_config=llm_config,
        displayer=displayer,
        t=locale_handler,
        chat_history=chat_history,
    )

    rendered = _rendered_text(mock_llm)
    for message in chat_history:
        assert message.content in rendered


@pytest.mark.asyncio
async def test_guard_with_empty_chat_history_still_calls_the_model(
    mock_llm, llm_config, displayer, run_context, locale_handler
):
    await do_context_sufficient_guard(
        user_query="What is the capital of France?",
        context_message=ChatMessage(role=MessageRole.USER, blocks=[TextBlock(text="Paris is the capital of France.")]),
        check_context_sufficiency=True,
        max_hops=3,
        run_context=run_context,
        llm_config=llm_config,
        displayer=displayer,
        t=locale_handler,
        chat_history=[],
    )

    assert mock_llm.achat.called


@pytest.mark.asyncio
async def test_guard_forwards_context_message_with_image_blocks_intact(
    mock_llm, llm_config, displayer, run_context, locale_handler
):
    """Regression: when retrieved context contains figures, the guard prompt must still carry the
    image block so the model can see it — not a flattened text-only string."""
    image_url = "https://example.com/figure.png"
    context_message = ChatMessage(
        role=MessageRole.USER,
        blocks=[
            TextBlock(text="<REFERENCE_DOCUMENT source='doc.pdf'>\n"),
            ImageBlock(url=image_url),
            TextBlock(text="</REFERENCE_DOCUMENT>\n"),
        ],
    )

    await do_context_sufficient_guard(
        user_query="What is shown in the figure?",
        context_message=context_message,
        check_context_sufficiency=True,
        max_hops=3,
        run_context=run_context,
        llm_config=llm_config,
        displayer=displayer,
        t=locale_handler,
        chat_history=[],
    )

    assert any(isinstance(block, ImageBlock) for block in _rendered_blocks(mock_llm))


@pytest.mark.asyncio
async def test_guard_emits_reject_event_when_no_more_hops(mock_llm, llm_config, displayer, run_context, locale_handler):
    mock_llm.achat = AsyncMock(return_value=_verdict_response("INSUFFICIENT Context does not answer the question"))

    result = await do_context_sufficient_guard(
        user_query="What is the meaning of life?",
        context_message=ChatMessage(role=MessageRole.USER, blocks=[TextBlock(text="Unrelated document.")]),
        check_context_sufficiency=True,
        max_hops=1,
        run_context=run_context,
        llm_config=llm_config,
        displayer=displayer,
        t=locale_handler,
        chat_history=[],
    )

    assert isinstance(result, ContextInsufficientRejectEvent)
    assert result.reason == "Context does not answer the question"
