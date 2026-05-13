from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest
from llama_index.core.base.llms.types import ChatMessage, ImageBlock, MessageRole, TextBlock
from swiss_ai_hub.core.events.agent import ContextInsufficientRejectEvent, ContextSufficientAcceptEvent
from swiss_ai_hub.core.generative_ai.chat_history.extend_chat_history_with_organization_memory import (
    extend_chat_history_with_organization_memory,
)
from swiss_ai_hub.core.generative_ai.guards.context_sufficient_guard import ContextGuardResult
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.infrastructure.mem0.types.memory import Memory
from swiss_ai_hub.core.infrastructure.mem0.types.memory_metadata import MemoryMetadata
from swiss_ai_hub.core.infrastructure.mem0.types.memory_type import MemoryType

from swiss_ai_hub.agent.rag.step_functions import do_context_sufficient_guard

_GUARD_PROMPT = LocaleString(
    en='{% chat role="user" %}TEST {{ user_query }}{% endchat %}',
    de='{% chat role="user" %}TEST {{ user_query }}{% endchat %}',
    fr='{% chat role="user" %}TEST {{ user_query }}{% endchat %}',
    it='{% chat role="user" %}TEST {{ user_query }}{% endchat %}',
)


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
        context_message=ChatMessage(role=MessageRole.USER, blocks=[TextBlock(text="Employee handbook chapter 3.")]),
        check_context_sufficiency=True,
        max_hops=3,
        run_context=run_context,
        llm_config=llm_config,
        displayer=displayer,
        t=locale_handler,
        chat_history=chat_history_with_memory,
        guard_prompt=_GUARD_PROMPT,
        guard_max_attempts=3,
    )

    forwarded_history = mock_llm.astructured_predict.call_args.kwargs["chat_history"]
    assert forwarded_history == chat_history_with_memory
    assert any(memory_text in (m.content or "") for m in forwarded_history)


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
        guard_prompt=_GUARD_PROMPT,
        guard_max_attempts=3,
    )

    forwarded = mock_llm.astructured_predict.call_args.kwargs["chat_history"]
    assert forwarded == chat_history


@pytest.mark.asyncio
async def test_guard_with_empty_chat_history_still_renders_empty_placeholder(
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
        guard_prompt=_GUARD_PROMPT,
        guard_max_attempts=3,
    )

    assert mock_llm.astructured_predict.call_args.kwargs["chat_history"] == []


@pytest.mark.asyncio
async def test_guard_forwards_context_message_with_image_blocks_intact(
    mock_llm, llm_config, displayer, run_context, locale_handler
):
    """Regression: when retrieved context contains figures, the guard must receive the rich
    ChatMessage so its LLM call can render the images — not a flattened text-only string."""
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
        guard_prompt=_GUARD_PROMPT,
        guard_max_attempts=3,
    )

    forwarded_blocks = mock_llm.astructured_predict.call_args.kwargs["context_blocks"]
    assert any(isinstance(block, ImageBlock) for block in forwarded_blocks)


@pytest.mark.asyncio
async def test_guard_emits_reject_event_when_no_more_hops(mock_llm, llm_config, displayer, run_context, locale_handler):
    mock_llm.astructured_predict = AsyncMock(
        return_value=ContextGuardResult(
            reasoning="Context does not answer the question",
            success=False,
            new_query=None,
        )
    )

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
        guard_prompt=_GUARD_PROMPT,
        guard_max_attempts=3,
    )

    assert isinstance(result, ContextInsufficientRejectEvent)
    assert result.reason == "Context does not answer the question"


@pytest.mark.asyncio
async def test_guard_retries_when_structured_predict_fails_then_succeeds(
    mock_llm, llm_config, displayer, run_context, locale_handler
):
    """When the first attempt produces malformed output the guard retries until it gets a valid result."""
    accept_result = ContextGuardResult(
        reasoning="Context is sufficient on retry",
        success=True,
        new_query=None,
    )
    mock_llm.astructured_predict = AsyncMock(
        side_effect=[
            ValueError("LLM returned plain text instead of a tool call"),
            accept_result,
        ]
    )

    result = await do_context_sufficient_guard(
        user_query="What is X?",
        context_message=ChatMessage(role=MessageRole.USER, blocks=[TextBlock(text="X is documented here.")]),
        check_context_sufficiency=True,
        max_hops=1,
        run_context=run_context,
        llm_config=llm_config,
        displayer=displayer,
        t=locale_handler,
        chat_history=[],
        guard_prompt=_GUARD_PROMPT,
        guard_max_attempts=3,
    )

    assert isinstance(result, ContextSufficientAcceptEvent)
    assert mock_llm.astructured_predict.await_count == 2


@pytest.mark.asyncio
async def test_guard_raises_after_max_attempts_of_malformed_output(
    mock_llm, llm_config, displayer, run_context, locale_handler
):
    """After max_attempts of malformed output the final error must propagate (fail-fast)."""
    mock_llm.astructured_predict = AsyncMock(side_effect=ValueError("still bad output"))

    with pytest.raises(ValueError, match="still bad output"):
        await do_context_sufficient_guard(
            user_query="What is X?",
            context_message=ChatMessage(role=MessageRole.USER, blocks=[TextBlock(text="Unrelated.")]),
            check_context_sufficiency=True,
            max_hops=1,
            run_context=run_context,
            llm_config=llm_config,
            displayer=displayer,
            t=locale_handler,
            chat_history=[],
            guard_prompt=_GUARD_PROMPT,
            guard_max_attempts=3,
        )

    assert mock_llm.astructured_predict.await_count == 3


@pytest.mark.asyncio
async def test_guard_uses_supplied_prompt(mock_llm, llm_config, displayer, run_context, locale_handler):
    """The guard_prompt LocaleString passed by the agent step is used as the LLM prompt template."""
    marker_text = "CUSTOM-GUARD-PROMPT-MARKER {{ user_query }}"
    custom_prompt = LocaleString(en=marker_text, de=marker_text, fr=marker_text, it=marker_text)

    await do_context_sufficient_guard(
        user_query="What is X?",
        context_message=ChatMessage(role=MessageRole.USER, blocks=[TextBlock(text="X is here.")]),
        check_context_sufficiency=True,
        max_hops=1,
        run_context=run_context,
        llm_config=llm_config,
        displayer=displayer,
        t=locale_handler,
        chat_history=[],
        guard_prompt=custom_prompt,
        guard_max_attempts=3,
    )

    forwarded_template = mock_llm.astructured_predict.call_args.args[1]
    assert "CUSTOM-GUARD-PROMPT-MARKER" in forwarded_template.template_str
