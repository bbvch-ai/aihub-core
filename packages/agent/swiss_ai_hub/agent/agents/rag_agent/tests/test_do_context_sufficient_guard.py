from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from llama_index.core.base.llms.types import ChatMessage, ChatResponse, ImageBlock, MessageRole, TextBlock
from llama_index.core.utils import get_tokenizer
from swiss_ai_hub.core.events.agent import ContextInsufficientRejectEvent
from swiss_ai_hub.core.generative_ai import LLMConfig, estimate_prompt_tokens
from swiss_ai_hub.core.generative_ai.chat_history.extend_chat_history_with_organization_memory import (
    extend_chat_history_with_organization_memory,
)
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.infrastructure.mem0.types.memory import Memory
from swiss_ai_hub.core.infrastructure.mem0.types.memory_metadata import MemoryMetadata
from swiss_ai_hub.core.infrastructure.mem0.types.memory_type import MemoryType
from swiss_ai_hub.core.testing.auth_utils import fake_user

from swiss_ai_hub.agent.agents.rag_agent.configs.rag_agent_config import RAGAgentConfig
from swiss_ai_hub.agent.capabilities.attached_files.attached_files_config import AttachedFilesConfig
from swiss_ai_hub.agent.capabilities.conversation.conversation_fields import ConversationFields
from swiss_ai_hub.agent.rag.step_functions import do_context_sufficient_guard
from swiss_ai_hub.agent.steps.guards.context_sufficient_guard_step.context_sufficient_guard_step_config import (
    ContextSufficientGuardStepConfig,
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
    async def ctx(_displayer, user=None):  # noqa: ARG001
        yield mock_llm

    config.cost_reporting_llm = ctx
    return config


@pytest.fixture
def displayer():
    d = MagicMock()
    d.display_thought = AsyncMock()
    d.display_llm_costs = AsyncMock()
    return d


# The agent's own counter, which `limit_chat_history` also uses: a test counting otherwise trims the history short
# of the budget and hides an overflow.
_token_counter = get_tokenizer()


def _conversation(input_budget: int) -> MagicMock:
    conversation = MagicMock()
    conversation.input_budget.return_value = input_budget
    conversation.llm.token_counter = _token_counter
    return conversation


@pytest.fixture
def conversation() -> MagicMock:
    return _conversation(input_budget=100_000)


@pytest.fixture
def run_context():
    ctx = MagicMock()
    ctx.get = AsyncMock(side_effect=lambda key, default=None: default)
    ctx.set = AsyncMock()
    return ctx


@pytest.mark.asyncio
async def test_organization_memory_system_message_reaches_guard_prompt(
    mock_llm, llm_config, displayer, run_context, locale_handler, conversation
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
        user=fake_user(),
        history=chat_history_with_memory,
        blocks=[],
        conversation=conversation,
    )

    assert memory_text in _rendered_text(mock_llm)


@pytest.mark.asyncio
async def test_guard_forwards_full_chat_history_including_user_and_assistant_turns(
    mock_llm, llm_config, displayer, run_context, locale_handler, conversation
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
        user=fake_user(),
        history=chat_history,
        blocks=[],
        conversation=conversation,
    )

    rendered = _rendered_text(mock_llm)
    for message in chat_history:
        assert message.content in rendered


@pytest.mark.asyncio
async def test_guard_with_empty_chat_history_still_calls_the_model(
    mock_llm, llm_config, displayer, run_context, locale_handler, conversation
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
        user=fake_user(),
        history=[],
        blocks=[],
        conversation=conversation,
    )

    assert mock_llm.achat.called


@pytest.mark.asyncio
async def test_guard_forwards_context_message_with_image_blocks_intact(
    mock_llm, llm_config, displayer, run_context, locale_handler, conversation
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
        user=fake_user(),
        history=[],
        blocks=[],
        conversation=conversation,
    )

    assert any(isinstance(block, ImageBlock) for block in _rendered_blocks(mock_llm))


@pytest.mark.asyncio
async def test_guard_emits_reject_event_when_no_more_hops(
    mock_llm, llm_config, displayer, run_context, locale_handler, conversation
):
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
        user=fake_user(),
        history=[],
        blocks=[],
        conversation=conversation,
    )

    assert isinstance(result, ContextInsufficientRejectEvent)
    assert result.reason == "Context does not answer the question"


def _long_conversation(turns: int, words_per_answer: int) -> list[ChatMessage]:
    history = [ChatMessage(role=MessageRole.SYSTEM, content="You are a helpful assistant.")]
    for turn in range(turns):
        history.append(ChatMessage(role=MessageRole.USER, content=f"Question {turn}"))
        history.append(ChatMessage(role=MessageRole.ASSISTANT, content=f"Answer{turn}: " + "word " * words_per_answer))
    history.append(ChatMessage(role=MessageRole.USER, content="Which torque applies on line 7?"))
    return history


def _documents(words: int) -> ChatMessage:
    return ChatMessage(role=MessageRole.USER, content="<REFERENCE_DOCUMENT>" + "document " * words)


@pytest.mark.asyncio
@pytest.mark.parametrize("more_hops", [True, False], ids=["with-hops-left", "last-hop"])
async def test_guard_prompt_stays_within_the_input_budget(
    mock_llm, llm_config, displayer, run_context, locale_handler, more_hops
):
    """Regression for #2077: the history used to be fitted to the whole budget, and the documents and the guard's
    instructions were rendered on top of it, so a long conversation overflowed by the size of the documents."""
    budget = 20_000
    run_context.get = AsyncMock(
        side_effect=lambda key, default=None: {"prev_queries": ["earlier query"], "hop_count": 1}.get(key, default)
    )

    await do_context_sufficient_guard(
        user_query="Which torque applies on line 7?",
        context_message=_documents(words=6_000),
        check_context_sufficiency=True,
        max_hops=3 if more_hops else 1,
        run_context=run_context,
        llm_config=llm_config,
        displayer=displayer,
        t=locale_handler,
        history=_long_conversation(turns=14, words_per_answer=2_000),
        blocks=[[ChatMessage(role=MessageRole.SYSTEM, content="memory " * 500)]],
        conversation=_conversation(input_budget=budget),
        user=fake_user(),
    )

    assert estimate_prompt_tokens(_prompt_messages(mock_llm), _token_counter) <= budget


@pytest.mark.asyncio
async def test_guard_keeps_the_documents_and_the_question_when_the_history_must_give_way(
    mock_llm, llm_config, displayer, run_context, locale_handler
):
    await do_context_sufficient_guard(
        user_query="Which torque applies on line 7?",
        context_message=_documents(words=6_000),
        check_context_sufficiency=True,
        max_hops=3,
        run_context=run_context,
        llm_config=llm_config,
        displayer=displayer,
        t=locale_handler,
        history=_long_conversation(turns=14, words_per_answer=2_000),
        blocks=[],
        conversation=_conversation(input_budget=20_000),
        user=fake_user(),
    )

    rendered = _rendered_text(mock_llm)
    assert rendered.count("document ") >= 6_000
    assert "Which torque applies on line 7?" in rendered
    assert "Answer0:" not in rendered
    assert "Answer13:" in rendered


def _guarded_rag_config() -> RAGAgentConfig:
    return RAGAgentConfig.model_construct(
        agent_id="rag",
        name=LocaleString(en="RAG"),
        llm=LLMConfig(model_name="text-generation/dummy"),
        retrievers=[],
        context_sufficient_guard=ContextSufficientGuardStepConfig(check_context_sufficiency=True, max_hops=3),
    )


def _attached_file(tokens: int) -> list[ChatMessage]:
    words = tokens
    while True:
        block = [ChatMessage(role=MessageRole.USER, content="<REFERENCE_DOCUMENT>" + "attached " * words)]
        excess = estimate_prompt_tokens(block, _token_counter) - tokens
        if excess <= 0:
            return block
        words -= excess


@pytest.mark.asyncio
async def test_guard_keeps_the_attached_file_rag_sized_when_the_documents_fit_their_reserve(
    mock_llm, llm_config, displayer, run_context, locale_handler
):
    """The files are read in parallel with retrieval, sized to the room left after the history and RAG's reserve.
    Without the guard's own instructions in that reserve, the file filled room the guard needs and was dropped from
    its prompt, so the guard judged without a file the answer step kept."""
    budget = 2_500
    query = "Which torque applies on line 7?"
    config = _guarded_rag_config()
    history = [
        ChatMessage(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
        ChatMessage(role=MessageRole.USER, content=query),
    ]
    documents = _documents(words=budget // 2)
    retrieved_reserve = estimate_prompt_tokens([documents], _token_counter)

    with patch.object(ConversationFields, "input_budget", return_value=budget):
        reserve = retrieved_reserve + config.context_sufficient_guard_reserve(locale_handler, query)
        share = AttachedFilesConfig.model_fields["share_of_input_budget"].default
        file_room = int((budget - estimate_prompt_tokens(history, _token_counter) - reserve) * share)

        await do_context_sufficient_guard(
            user_query=query,
            context_message=documents,
            check_context_sufficiency=True,
            max_hops=3,
            run_context=run_context,
            llm_config=llm_config,
            displayer=displayer,
            t=locale_handler,
            history=history,
            blocks=[_attached_file(file_room)],
            conversation=config,
            user=fake_user(),
        )

        assert estimate_prompt_tokens(_prompt_messages(mock_llm), _token_counter) <= budget
    rendered = _rendered_text(mock_llm)
    assert "attached " in rendered
    assert rendered.count("document ") >= budget // 2
