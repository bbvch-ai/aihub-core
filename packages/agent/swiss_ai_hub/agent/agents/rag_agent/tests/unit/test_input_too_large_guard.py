"""The input-size guard that turns an oversized upload into a refusal instead of a provider 400.

Reproduces aihub-core-private#241: OpenWebUI runs with `RAG_FULL_CONTEXT` and prepends a whole document into the
user message, which no truncation removes -- `ChatMemoryBuffer` keeps the most recent message whatever its size.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from llama_index.core.base.llms.types import ChatMessage, ImageBlock, MessageRole
from swiss_ai_hub.core.events.agent import LimitChatHistoryEvent, RAGFailureReason, RAGFailureStopEvent
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler

# Load rag_agent first: it has a module-level circular dependency with rag.preconditions/step_functions that only
# resolves in the runtime (rag_agent-first) order; importing step_functions first would break.
import swiss_ai_hub.agent.agents.rag_agent  # noqa: F401  (import-order guard, not a direct dependency)
from swiss_ai_hub.agent.rag.step_functions import do_limit_chat_history

MODEL_WINDOW = 100_000

# One token per repetition under tiktoken, so a message's size is the count of these.
TOKEN_WORD = " hello"


def _message(tokens: int, role: MessageRole = MessageRole.USER) -> ChatMessage:
    return ChatMessage(role=role, content=TOKEN_WORD * tokens)


def _locale_handler() -> LocaleHandler:
    return LocaleHandler(locale="en")


def _displayer() -> MagicMock:
    displayer = MagicMock()
    displayer.display_thought = AsyncMock()
    displayer.display_chunk = AsyncMock()
    return displayer


def _llm_config(model_name: str = "text-generation/gemma-4-31B-it") -> LLMConfig:
    return LLMConfig(model_name=model_name)


def _with_window(*windows: int | None):
    """Patch the LiteLLM lookup, which is a module-level lru_cache over a real HTTP GET."""
    infos = [{"model_info": {} if window is None else {"max_input_tokens": window}} for window in windows]
    return patch.object(LLMConfig, "get_model_info", side_effect=infos * 10)


async def _run(
    messages: list[ChatMessage],
    last_user_message: ChatMessage,
    displayer: MagicMock,
    windows=(MODEL_WINDOW, MODEL_WINDOW),
):
    with _with_window(*windows):
        return await do_limit_chat_history(
            messages,
            128_000,
            last_user_message,
            [_llm_config(), _llm_config()],
            displayer,
            _locale_handler(),
        )


class TestAnInputThatFitsIsUntouched:
    @pytest.mark.asyncio
    async def test_a_short_conversation_passes_through(self):
        history = [_message(10), _message(10, MessageRole.ASSISTANT), _message(10)]
        displayer = _displayer()

        result = await _run(history, history[-1], displayer)

        assert isinstance(result, LimitChatHistoryEvent)
        displayer.display_chunk.assert_not_called()

    @pytest.mark.asyncio
    async def test_a_long_but_trimmable_history_is_trimmed_rather_than_refused(self):
        """The guard must not refuse what truncation can still fix, or every long conversation dies."""
        history = [_message(2_000) for _ in range(60)]
        displayer = _displayer()

        result = await _run(history, history[-1], displayer)

        assert isinstance(result, LimitChatHistoryEvent)
        assert len(result.limited_history) < len(history)
        displayer.display_chunk.assert_not_called()


class TestAnInputTooLargeForTheModelIsRefused:
    @pytest.mark.asyncio
    async def test_a_single_oversized_turn_stops_the_run(self):
        oversized = _message(200_000)
        displayer = _displayer()

        result = await _run([oversized], oversized, displayer)

        assert isinstance(result, RAGFailureStopEvent)
        assert result.reason == RAGFailureReason.INPUT_TOO_LARGE

    @pytest.mark.asyncio
    async def test_the_refusal_is_streamed_to_the_user_and_carried_on_the_event(self):
        """`display_chunk` is what the chat shows; `answer` is what non-streaming consumers read."""
        oversized = _message(200_000)
        displayer = _displayer()

        result = await _run([oversized], oversized, displayer)

        displayer.display_chunk.assert_awaited_once()
        assert displayer.display_chunk.await_args.args[0] == result.answer
        assert "too large" in result.answer
        displayer.display_thought.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_a_turn_that_merely_strains_the_window_is_left_to_the_model(self):
        """The threshold is the impossible case, not a prediction of any one step's prompt. tiktoken is not the
        served model's tokenizer and over-counts non-Latin scripts enough that budgeting for the downstream
        doubling refuses prompts the provider accepts -- 121k tiktoken tokens of Vietnamese fit a declared 100k
        window, measured against gemma-4-31B-it. Such a prompt gets the provider's own (now rewritten) 400."""
        turn = _message(int(MODEL_WINDOW * 0.6))
        displayer = _displayer()

        result = await _run([turn], turn, displayer)

        assert isinstance(result, LimitChatHistoryEvent)
        displayer.display_chunk.assert_not_called()

    @pytest.mark.asyncio
    async def test_the_narrower_of_the_two_model_windows_decides(self):
        """One prompt is handed to whichever model each step uses, so the widest window cannot be the budget."""
        turn = _message(30_000)
        displayer = _displayer()

        assert isinstance(
            await _run([turn], turn, displayer, windows=(MODEL_WINDOW, MODEL_WINDOW)), LimitChatHistoryEvent
        )
        assert isinstance(await _run([turn], turn, _displayer(), windows=(MODEL_WINDOW, 8_192)), RAGFailureStopEvent)


class TestAnUnknownWindowLeavesTheRunAlone:
    """A guard must never convert a working run into a failing one."""

    @pytest.mark.asyncio
    async def test_a_model_missing_from_litellm_skips_the_check(self):
        oversized = _message(200_000)
        displayer = _displayer()

        with patch.object(LLMConfig, "get_model_info", side_effect=ValueError("Model x not found in LiteLLM Proxy.")):
            result = await do_limit_chat_history(
                [oversized], 128_000, oversized, [_llm_config()], displayer, _locale_handler()
            )

        assert isinstance(result, LimitChatHistoryEvent)
        displayer.display_chunk.assert_not_called()

    @pytest.mark.asyncio
    async def test_a_model_declaring_no_window_skips_the_check(self):
        oversized = _message(200_000)
        displayer = _displayer()

        result = await _run([oversized], oversized, displayer, windows=(None, None))

        assert isinstance(result, LimitChatHistoryEvent)

    @pytest.mark.asyncio
    async def test_a_window_that_is_not_a_positive_int_skips_the_check(self):
        """`model_info` is an untyped dict off the gateway, so a window is usable only once it proves to be one."""
        oversized = _message(200_000)

        for declared in ("100000", 0, -1):
            displayer = _displayer()
            with patch.object(LLMConfig, "get_model_info", return_value={"model_info": {"max_input_tokens": declared}}):
                result = await do_limit_chat_history(
                    [oversized], 128_000, oversized, [_llm_config()], displayer, _locale_handler()
                )

            assert isinstance(result, LimitChatHistoryEvent), f"declared={declared!r} must fail open"


class TestImagesAreCountedWithoutBeingFetched:
    @pytest.mark.asyncio
    async def test_an_unreachable_image_costs_no_network_call(self):
        """llama-index's own estimator resolves an ImageBlock -- downloading it -- purely to return a constant. A
        guard that exists to avoid one wasted call must not spend a round trip deciding."""
        message = ChatMessage(role=MessageRole.USER, blocks=[ImageBlock(url="https://unreachable.invalid/x.png")])
        displayer = _displayer()

        with patch.object(ImageBlock, "resolve_image", side_effect=AssertionError("image must not be resolved")):
            result = await _run([message], message, displayer)

        assert isinstance(result, LimitChatHistoryEvent)
