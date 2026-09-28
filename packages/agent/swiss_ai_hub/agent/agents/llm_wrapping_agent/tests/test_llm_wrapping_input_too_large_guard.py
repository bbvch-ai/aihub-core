"""The input-size guard on the LLM-wrapping blueprint, which has no provider-400 net to fall back on.

`RAGAgent` can let an oversized prompt reach the provider: its condense call is unstreamed, so LiteLLM relays the
provider's "maximum context length is N tokens" and `ModelGatewayErrorHandler` rewrites it. This agent answers
through `astream_chat`, and on a streaming call LiteLLM replaces that message with its own bookkeeping -- verified
against gemma-4-31B-it, where the identical prompt returns the limit unstreamed and a bare "Error code: 400"
streamed. So the refusal has to happen in the step or the user sees raw gateway internals.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from llama_index.core.base.llms.types import ChatMessage, ImageBlock, MessageRole
from swiss_ai_hub.core.events.agent import (
    LimitChatHistoryEvent,
    LLMStopEvent,
    NotAMetaQuestionEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.testing.auth_utils import fake_user

from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent import LLMWrappingAgent
from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent_config import LLMWrappingAgentConfig

MODEL_WINDOW = 100_000

# One token per repetition under tiktoken, so a message's size is the count of these.
TOKEN_WORD = " hello"


def _message(tokens: int, role: MessageRole = MessageRole.USER) -> ChatMessage:
    return ChatMessage(role=role, content=TOKEN_WORD * tokens)


def _displayer() -> MagicMock:
    displayer = MagicMock()
    displayer.display_thought = AsyncMock()
    displayer.display_chunk = AsyncMock()
    return displayer


def _config(number_of_input_tokens: int = 100_000) -> LLMWrappingAgentConfig:
    return LLMWrappingAgentConfig(
        agent_id="instructed-agent",
        name=LocaleString(en="Instructed Assistant"),
        description=LocaleString(en="Follows plain-text instructions"),
        system_prompt=LocaleString(en="You are helpful."),
        number_of_input_tokens=number_of_input_tokens,
        llm=LLMConfig(model_name="text-generation/gemma-4-31B-it"),
    )


def _with_window(*windows: int | str | None):
    """Patch the LiteLLM lookup, which is a module-level lru_cache over a real HTTP GET."""
    infos = [{"model_info": {} if window is None else {"max_input_tokens": window}} for window in windows]
    return patch.object(LLMConfig, "get_model_info", side_effect=infos * 10)


async def _run(
    messages: list[ChatMessage],
    displayer: MagicMock,
    windows: tuple[int | str | None, ...] = (MODEL_WINDOW, MODEL_WINDOW),
    number_of_input_tokens: int = 100_000,
):
    with _with_window(*windows):
        return await LLMWrappingAgent().limit_chat_history_step(
            event=UserMessageEvent(user=fake_user(), messages=messages),
            agent_config=_config(number_of_input_tokens),
            displayer=displayer,
            t=LocaleHandler(locale="en"),
            _clear=NotAMetaQuestionEvent(reasoning="not a meta question"),
        )


class TestAnInputThatFitsIsUntouched:
    @pytest.mark.asyncio
    async def test_a_short_conversation_passes_through(self):
        displayer = _displayer()

        result = await _run([_message(10), _message(10, MessageRole.ASSISTANT), _message(10)], displayer)

        assert isinstance(result, LimitChatHistoryEvent)
        displayer.display_chunk.assert_not_called()

    @pytest.mark.asyncio
    async def test_the_configured_system_prompt_still_leads_the_history(self):
        """The guard runs after the prompt is assembled, so it must not disturb the assembly."""
        result = await _run([_message(10)], _displayer())

        assert isinstance(result, LimitChatHistoryEvent)
        assert result.limited_history[0].role == MessageRole.SYSTEM
        assert "You are helpful." in (result.limited_history[0].content or "")

    @pytest.mark.asyncio
    async def test_a_long_but_trimmable_history_is_trimmed_rather_than_refused(self):
        """The guard must not refuse what truncation can still fix, or every long conversation dies."""
        displayer = _displayer()
        turns = [_message(2_000, MessageRole.USER if index % 2 == 0 else MessageRole.ASSISTANT) for index in range(60)]

        result = await _run(turns, displayer)

        assert isinstance(result, LimitChatHistoryEvent)
        assert len(result.limited_history) < len(turns)
        displayer.display_chunk.assert_not_called()

    @pytest.mark.asyncio
    async def test_the_system_prompt_survives_a_history_long_enough_to_trim(self):
        """`ChatMemoryBuffer` keeps the most recent messages with no regard for role, so a system prompt left in
        the list it trims is dropped by any conversation that overflows -- leaving this blueprint, whose whole
        purpose is following the operator's instructions, silently uninstructed partway through a chat."""
        turns = [_message(2_000, MessageRole.USER if index % 2 == 0 else MessageRole.ASSISTANT) for index in range(60)]

        result = await _run(turns, _displayer())

        assert isinstance(result, LimitChatHistoryEvent)
        assert len(result.limited_history) < len(turns), "the history must actually have been trimmed"
        assert result.limited_history[0].role == MessageRole.SYSTEM
        assert "You are helpful." in (result.limited_history[0].content or "")

    @pytest.mark.asyncio
    async def test_the_system_prompt_survives_the_fail_open_path_too(self):
        """An unestablished window must not also mean an uninstructed agent."""
        turns = [_message(2_000, MessageRole.USER if index % 2 == 0 else MessageRole.ASSISTANT) for index in range(60)]

        result = await _run(turns, _displayer(), windows=(None, None), number_of_input_tokens=40_000)

        assert isinstance(result, LimitChatHistoryEvent)
        assert len(result.limited_history) < len(turns)
        assert result.limited_history[0].role == MessageRole.SYSTEM

    @pytest.mark.asyncio
    async def test_the_last_turn_survives_a_history_long_enough_to_trim(self):
        """The question being answered is as irreducible as the instructions."""
        # An even count leaves an assistant turn last, so the appended user message stays a message of its own
        # rather than being merged into it.
        turns = [_message(2_000, MessageRole.USER if index % 2 == 0 else MessageRole.ASSISTANT) for index in range(60)]
        final = _message(2_000)

        result = await _run([*turns, final], _displayer())

        assert isinstance(result, LimitChatHistoryEvent)
        assert result.limited_history[-1].content == final.content

    @pytest.mark.asyncio
    async def test_consecutive_same_role_turns_are_judged_as_the_one_message_they_become(self):
        """This step merges same-role neighbours before the guard runs -- strict providers (Qwen3.5 on Infomaniak)
        reject a system message past index 0, so the history is flattened first. A client that sends many
        consecutive user turns therefore presents one irreducible message, and it is judged as such. Real chat
        clients alternate roles, so this only bites a caller that does not."""
        result = await _run([_message(20_000, MessageRole.USER) for _ in range(6)], _displayer())

        assert isinstance(result, LLMStopEvent)


class TestAnInputTooLargeForTheModelIsRefused:
    @pytest.mark.asyncio
    async def test_a_single_oversized_turn_stops_the_run(self):
        """The reproduction: OpenWebUI under `RAG_FULL_CONTEXT` pastes a whole PDF into one turn, which no
        truncation removes -- `ChatMemoryBuffer.get` falls through to `chat_history[-1:]` when one message alone
        exceeds the limit (llama-index-core 0.14.22)."""
        displayer = _displayer()

        result = await _run([_message(200_000)], displayer)

        assert isinstance(result, LLMStopEvent)

    @pytest.mark.asyncio
    async def test_the_refusal_is_streamed_and_readable_by_non_streaming_consumers(self):
        """`display_chunk` is what the chat shows; `output_messages` is what `OpenaiService` reads off the
        terminal event."""
        displayer = _displayer()

        result = await _run([_message(200_000)], displayer)

        assert isinstance(result, LLMStopEvent)
        refusal = result.output_messages[-1].content
        displayer.display_chunk.assert_awaited_once()
        assert displayer.display_chunk.await_args.args[0] == refusal
        assert "too large" in refusal
        displayer.display_thought.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_the_refusal_names_the_model_that_could_not_take_it(self):
        result = await _run([_message(200_000)], _displayer())

        assert isinstance(result, LLMStopEvent)
        assert result.chat_model_name == "text-generation/gemma-4-31B-it"

    @pytest.mark.asyncio
    async def test_no_model_call_is_made(self):
        """The whole point: entering `cost_reporting_llm` mints a per-user gateway key over HTTP before the
        doomed call is even sent."""
        with patch.object(LLMConfig, "cost_reporting_llm", side_effect=AssertionError("no model call expected")):
            result = await _run([_message(200_000)], _displayer())

        assert isinstance(result, LLMStopEvent)

    @pytest.mark.asyncio
    async def test_a_turn_that_merely_strains_the_window_is_left_to_the_model(self):
        """The threshold is the impossible case, not a prediction of the prompt any one step builds. tiktoken is
        not the served model's tokenizer and over-counts non-Latin scripts enough that budgeting for downstream
        overhead refuses prompts the provider accepts -- 121k tiktoken tokens of Vietnamese fit a declared 100k
        window, measured against gemma-4-31B-it."""
        displayer = _displayer()

        result = await _run([_message(int(MODEL_WINDOW * 0.6))], displayer)

        assert isinstance(result, LimitChatHistoryEvent)
        assert result.limited_history, "the user's question must survive truncation"
        displayer.display_chunk.assert_not_called()

    @pytest.mark.asyncio
    async def test_a_large_turn_does_not_cost_the_earlier_conversation(self):
        """Reserving room for the last turn must not also charge the trimmer for it. A turn past half the budget
        would otherwise leave no subset containing it under the reduced limit, and every earlier message would be
        dropped -- losing the conversation for the title and follow-up questions."""
        turn = _message(60_000)
        older = [_message(5_000), _message(5_000, MessageRole.ASSISTANT)]

        result = await _run([*older, turn], _displayer())

        assert isinstance(result, LimitChatHistoryEvent)
        assert result.limited_history[-1].content == turn.content
        assert len(result.limited_history) > 1, "the earlier conversation must survive a large final turn"

    @pytest.mark.asyncio
    async def test_the_narrower_of_the_answer_and_task_model_windows_decides(self):
        """One prompt is built once and handed to the answering model and to conversation-metadata generation, so
        the widest window cannot be the budget."""
        turn = [_message(30_000)]

        assert isinstance(await _run(turn, _displayer(), windows=(MODEL_WINDOW, MODEL_WINDOW)), LimitChatHistoryEvent)
        assert isinstance(await _run(turn, _displayer(), windows=(MODEL_WINDOW, 8_192)), LLMStopEvent)

    @pytest.mark.asyncio
    async def test_the_cost_ceiling_does_not_raise_the_refusal_threshold(self):
        """`number_of_input_tokens` is an admin's cost ceiling and may sit above the model's real window; only
        the window can decide what the provider will accept."""
        result = await _run([_message(200_000)], _displayer(), number_of_input_tokens=500_000)

        assert isinstance(result, LLMStopEvent)


class TestAnUnknownWindowLeavesTheRunAlone:
    """A guard must never convert a working run into a failing one."""

    @pytest.mark.asyncio
    async def test_a_model_missing_from_litellm_skips_the_check(self):
        displayer = _displayer()

        with patch.object(LLMConfig, "get_model_info", side_effect=ValueError("Model x not found in LiteLLM Proxy.")):
            result = await LLMWrappingAgent().limit_chat_history_step(
                event=UserMessageEvent(user=fake_user(), messages=[_message(200_000)]),
                agent_config=_config(),
                displayer=displayer,
                t=LocaleHandler(locale="en"),
                _clear=NotAMetaQuestionEvent(reasoning="not a meta question"),
            )

        assert isinstance(result, LimitChatHistoryEvent)
        displayer.display_chunk.assert_not_called()

    @pytest.mark.asyncio
    async def test_a_model_declaring_no_window_skips_the_check(self):
        result = await _run([_message(200_000)], _displayer(), windows=(None, None))

        assert isinstance(result, LimitChatHistoryEvent)

    @pytest.mark.asyncio
    async def test_a_window_that_is_not_a_positive_int_skips_the_check(self):
        """`model_info` is an untyped dict off the gateway, so a window is usable only once it proves to be one."""
        for declared in ("100000", 0, -1):
            result = await _run([_message(200_000)], _displayer(), windows=(declared, declared))

            assert isinstance(result, LimitChatHistoryEvent), f"declared={declared!r} must fail open"


class TestImagesAreCountedWithoutBeingFetched:
    @pytest.mark.asyncio
    async def test_an_unreachable_image_costs_no_network_call(self):
        """llama-index's own estimator resolves an ImageBlock -- downloading it -- purely to return a constant. A
        guard that exists to avoid one wasted call must not spend a round trip deciding."""
        message = ChatMessage(role=MessageRole.USER, blocks=[ImageBlock(url="https://unreachable.invalid/x.png")])

        with patch.object(ImageBlock, "resolve_image", side_effect=AssertionError("image must not be resolved")):
            result = await _run([message], _displayer())

        assert isinstance(result, LimitChatHistoryEvent)
