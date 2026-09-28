"""The input-size guard on the few-shot blueprint.

Without it, an uploaded file that OpenWebUI pastes into the chat reaches the task model through the suitability guard,
and the provider's 400 surfaces as an error banner instead of an answer (issue #277).
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent import (
    LimitChatHistoryEvent,
    LLMStopEvent,
    NotAMetaQuestionEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.generative_ai import FewShotExample, LLMConfig
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.testing.auth_utils import fake_user

from swiss_ai_hub.agent.agents.few_shot_agent.few_shot_agent import FewShotAgent
from swiss_ai_hub.agent.agents.few_shot_agent.few_shot_agent_config import FewShotAgentConfig
from swiss_ai_hub.agent.steps.prompting.few_shot_step.few_shot_step_config import FewShotStepConfig

MODEL_WINDOW = 100_000

# One token per repetition under tiktoken, so a message's size is the count of these.
TOKEN_WORD = " hello"


def _message(tokens: int, role: MessageRole = MessageRole.USER) -> ChatMessage:
    return ChatMessage(role=role, content=TOKEN_WORD * tokens)


def _alternating_turns(count: int, tokens: int) -> list[ChatMessage]:
    return [_message(tokens, MessageRole.USER if index % 2 == 0 else MessageRole.ASSISTANT) for index in range(count)]


def _displayer() -> MagicMock:
    displayer = MagicMock()
    displayer.display_thought = AsyncMock()
    displayer.display_chunk = AsyncMock()
    return displayer


def _config(number_of_input_tokens: int = 100_000) -> FewShotAgentConfig:
    return FewShotAgentConfig(
        agent_id="teachable-agent",
        name=LocaleString(en="Teachable Assistant"),
        description=LocaleString(en="Answers fashion questions"),
        number_of_input_tokens=number_of_input_tokens,
        llm=LLMConfig(model_name="text-generation/gemma-4-31B-it"),
        few_shot=FewShotStepConfig(
            few_shot_examples=[FewShotExample(user=LocaleString(en="hi"), agent=LocaleString(en="hello"))],
            system_prompt=LocaleString(en="Respond briefly."),
        ),
    )


def _with_window(*windows: int | None):
    """Patch the LiteLLM lookup, which is a module-level lru_cache over a real HTTP GET."""
    infos = [{"model_info": {} if window is None else {"max_input_tokens": window}} for window in windows]
    return patch.object(LLMConfig, "get_model_info", side_effect=infos * 10)


async def _run(
    messages: list[ChatMessage],
    displayer: MagicMock,
    windows: tuple[int | None, ...] = (MODEL_WINDOW, MODEL_WINDOW),
    number_of_input_tokens: int = 100_000,
) -> LimitChatHistoryEvent | LLMStopEvent:
    with _with_window(*windows):
        return await FewShotAgent().limit_chat_history_step(
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
        messages = [_message(10), _message(10, MessageRole.ASSISTANT), _message(10)]

        result = await _run(messages, displayer)

        assert isinstance(result, LimitChatHistoryEvent)
        assert [msg.content for msg in result.limited_history] == [msg.content for msg in messages]
        displayer.display_chunk.assert_not_called()

    @pytest.mark.asyncio
    async def test_a_long_but_trimmable_history_is_trimmed_rather_than_refused(self):
        turns = _alternating_turns(60, 2_000)
        final = _message(2_000)

        result = await _run([*turns, final], _displayer())

        assert isinstance(result, LimitChatHistoryEvent)
        assert len(result.limited_history) < len(turns)
        assert result.limited_history[-1].content == final.content

    @pytest.mark.asyncio
    async def test_client_system_messages_survive_trimming(self):
        system = ChatMessage(role=MessageRole.SYSTEM, content="Client instructions.")

        result = await _run([system, *_alternating_turns(60, 2_000), _message(10)], _displayer())

        assert isinstance(result, LimitChatHistoryEvent)
        assert result.limited_history[0].content == "Client instructions."

    @pytest.mark.asyncio
    async def test_a_large_turn_does_not_cost_the_earlier_conversation(self):
        turn = _message(60_000)

        result = await _run([_message(5_000), _message(5_000, MessageRole.ASSISTANT), turn], _displayer())

        assert isinstance(result, LimitChatHistoryEvent)
        assert result.limited_history[-1].content == turn.content
        assert len(result.limited_history) > 1


class TestAnInputTooLargeForTheModelIsRefused:
    @pytest.mark.asyncio
    async def test_an_oversized_file_in_the_last_turn_is_refused_with_a_reply(self):
        displayer = _displayer()

        result = await _run([_message(200_000)], displayer)

        assert isinstance(result, LLMStopEvent)
        refusal = result.output_messages[-1].content
        displayer.display_chunk.assert_awaited_once()
        assert displayer.display_chunk.await_args.args[0] == refusal
        displayer.display_thought.assert_awaited_once()
        assert result.chat_model_name == "text-generation/gemma-4-31B-it"

    @pytest.mark.asyncio
    async def test_the_refusal_does_not_promise_to_read_a_smaller_file(self):
        """This blueprint answers from its examples, never from the document, so the other blueprints' advice to
        upload a smaller file would be wrong here."""
        result = await _run([_message(200_000)], _displayer())

        assert isinstance(result, LLMStopEvent)
        refusal = result.output_messages[-1].content
        assert "do not read attached documents" in refusal
        assert "smaller file" not in refusal

    @pytest.mark.asyncio
    async def test_an_oversized_file_in_a_system_message_is_refused(self):
        """OpenWebUI can inject file text as system context, which every step forwards untrimmed."""
        result = await _run([_message(200_000, MessageRole.SYSTEM), _message(10)], _displayer())

        assert isinstance(result, LLMStopEvent)

    @pytest.mark.asyncio
    async def test_no_model_call_is_made(self):
        with patch.object(LLMConfig, "cost_reporting_llm", side_effect=AssertionError("no model call expected")):
            result = await _run([_message(200_000)], _displayer())

        assert isinstance(result, LLMStopEvent)

    @pytest.mark.asyncio
    async def test_the_narrower_of_the_answer_and_task_model_windows_decides(self):
        turn = [_message(30_000)]

        assert isinstance(await _run(turn, _displayer(), windows=(MODEL_WINDOW, MODEL_WINDOW)), LimitChatHistoryEvent)
        assert isinstance(await _run(turn, _displayer(), windows=(MODEL_WINDOW, 8_192)), LLMStopEvent)

    @pytest.mark.asyncio
    async def test_the_cost_ceiling_does_not_raise_the_refusal_threshold(self):
        result = await _run([_message(200_000)], _displayer(), number_of_input_tokens=500_000)

        assert isinstance(result, LLMStopEvent)


class TestAnUnknownWindowLeavesTheRunAlone:
    @pytest.mark.asyncio
    async def test_a_model_declaring_no_window_skips_the_check(self):
        displayer = _displayer()

        result = await _run([_message(200_000)], displayer, windows=(None, None))

        assert isinstance(result, LimitChatHistoryEvent)
        displayer.display_chunk.assert_not_called()
