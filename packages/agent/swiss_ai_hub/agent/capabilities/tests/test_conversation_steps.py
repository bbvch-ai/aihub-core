"""The conversation capability's steps on their own, without infrastructure."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent import (
    CompleteConversationEvent,
    ComposeContextEvent,
    ContextualizeConversationEvent,
    ConversationContextualizedEvent,
    LLMEvent,
    LLMStopEvent,
    Message,
    NotAMetaQuestionEvent,
    RAGSuccessStopEvent,
    StandaloneQuestionCondenserEvent,
)
from swiss_ai_hub.core.generative_ai import LLMConfig, merge_consecutive_messages
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent import LLMWrappingAgent
from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent_config import LLMWrappingAgentConfig
from swiss_ai_hub.agent.capabilities.conversation.conversation import Conversation

CONVERSATION_MODULE = "swiss_ai_hub.agent.capabilities.conversation.conversation"
TOKEN_WORD = " hello"


def _config(*, condense: bool = False, number_of_input_tokens: int = 100_000) -> LLMWrappingAgentConfig:
    return LLMWrappingAgentConfig(
        agent_id="conversation-test",
        name=LocaleString(en="Conversation"),
        description=LocaleString(en="Conversation fixture"),
        system_prompt=LocaleString(en="You are helpful."),
        llm=LLMConfig(model_name="text-generation/gemma-4-31B-it"),
        number_of_input_tokens=number_of_input_tokens,
        condense_question=condense,
    )


def _message(role: MessageRole, tokens: int) -> ChatMessage:
    return ChatMessage(role=role, content=TOKEN_WORD * tokens)


def _no_window():
    return patch.object(LLMConfig, "get_model_info", return_value={"model_info": {}})


@pytest.mark.asyncio
async def test_a_programmatic_start_is_cleared_without_inspection():
    with patch(f"{CONVERSATION_MODULE}.do_detect_meta_question", new=AsyncMock()) as detect:
        cleared = await Conversation.inspect_message_step(
            LLMWrappingAgent(),
            request=ContextualizeConversationEvent(history=[], user_query=None),
            conversation=_config(),
            displayer=MagicMock(),
            t=MagicMock(),
        )

    detect.assert_not_awaited()
    assert isinstance(cleared, NotAMetaQuestionEvent)


@pytest.mark.asyncio
async def test_the_query_is_the_last_message_verbatim_unless_condensation_is_on():
    request = Conversation.contextualize(
        history=[
            ChatMessage(role=MessageRole.SYSTEM, content="be brief"),
            ChatMessage(role=MessageRole.USER, content="  what is the vacation policy? "),
        ]
    )
    events = await Conversation.derive_query_step(
        LLMWrappingAgent(),
        request=request,
        _cleared=NotAMetaQuestionEvent(reasoning=""),
        conversation=_config(),
        displayer=MagicMock(),
        t=MagicMock(),
    )

    assert [type(event) for event in events] == [ConversationContextualizedEvent]
    assert events[0].query == "  what is the vacation policy? "
    assert events[0].history == request.history
    assert events[0].condensed is False


@pytest.mark.asyncio
async def test_condensation_emits_the_display_event_and_the_result_together():
    request = Conversation.contextualize(history=[ChatMessage(role=MessageRole.USER, content="and in 2027?")])
    condensed = ChatMessage(role=MessageRole.USER, content="What is the vacation policy in 2027?")
    reporting = MagicMock()
    reporting.__aenter__ = AsyncMock(return_value=MagicMock())
    reporting.__aexit__ = AsyncMock(return_value=False)

    with (
        patch.object(LLMConfig, "cost_reporting_llm", return_value=reporting),
        patch(f"{CONVERSATION_MODULE}.condense_standalone_question", new=AsyncMock(return_value=condensed)),
    ):
        events = await Conversation.derive_query_step(
            LLMWrappingAgent(),
            request=request,
            _cleared=NotAMetaQuestionEvent(reasoning=""),
            conversation=_config(condense=True),
            displayer=MagicMock(display_thought=AsyncMock()),
            t=MagicMock(),
        )

    assert [type(event) for event in events] == [StandaloneQuestionCondenserEvent, ConversationContextualizedEvent]
    assert events[1].query == condensed.content
    assert events[1].condensed is True


@pytest.mark.asyncio
async def test_compose_puts_blocks_behind_the_system_head_in_order_and_trims_them_first():
    system = _message(MessageRole.SYSTEM, 10)
    turn = _message(MessageRole.USER, 20)
    first = [_message(MessageRole.SYSTEM, 30)]
    second = [_message(MessageRole.SYSTEM, 30)]

    with _no_window():
        composed = await Conversation.compose_context_step(
            LLMWrappingAgent(),
            request=Conversation.compose([system, turn], blocks=[first, second]),
            conversation=_config(number_of_input_tokens=1_000),
        )
        assert composed.history == [*merge_consecutive_messages([system, first[0], second[0]]), turn]
        assert [message.role for message in composed.history] == [MessageRole.SYSTEM, MessageRole.USER], (
            "the context leaves as one system message, which served models read in full"
        )

        trimmed = await Conversation.compose_context_step(
            LLMWrappingAgent(),
            request=Conversation.compose([system, turn], blocks=[first, second]),
            conversation=_config(number_of_input_tokens=60),
        )
        assert trimmed.history == [system, turn], "the blocks give way, never the turn or the head"


@pytest.mark.asyncio
async def test_compose_trims_the_oldest_turns_before_any_block():
    """A large attached file and the retrieved documents were asked for this turn; old turns are what gives way."""
    system = _message(MessageRole.SYSTEM, 10)
    older = [_message(MessageRole.USER if index % 2 == 0 else MessageRole.ASSISTANT, 100) for index in range(8)]
    question = _message(MessageRole.USER, 20)
    attached_file = [_message(MessageRole.SYSTEM, 300)]
    documents = [_message(MessageRole.SYSTEM, 300)]

    with _no_window():
        composed = await Conversation.compose_context_step(
            LLMWrappingAgent(),
            request=Conversation.compose([system, *older, question], blocks=[attached_file, documents]),
            conversation=_config(number_of_input_tokens=900),
        )

    head, *turns = composed.history
    assert head.content.count(TOKEN_WORD.strip()) == 610, "the file and the documents both stay in the prompt"
    assert turns[-1] == question
    assert 0 < len(turns) - 1 < len(older), "only the oldest turns gave way"
    assert turns[:-1] == older[-(len(turns) - 1) :]


@pytest.mark.asyncio
async def test_compose_passes_the_history_through_when_every_block_is_empty():
    history = [_message(MessageRole.USER, 5)]
    composed = await Conversation.compose_context_step(
        LLMWrappingAgent(),
        request=ComposeContextEvent(history=history, blocks=[[], []]),
        conversation=_config(),
    )
    assert composed.history == history


@pytest.mark.asyncio
async def test_compose_re_limits_instructions_added_to_the_history_even_without_blocks():
    """A rejection prompt ahead of an already-limited history must not push the prompt past the budget."""
    instructions = _message(MessageRole.SYSTEM, 200)
    older = [_message(MessageRole.USER, 100), _message(MessageRole.ASSISTANT, 100)]
    question = _message(MessageRole.USER, 20)

    with _no_window():
        composed = await Conversation.compose_context_step(
            LLMWrappingAgent(),
            request=ComposeContextEvent(history=[instructions, *older, question], blocks=[[], []]),
            conversation=_config(number_of_input_tokens=300),
        )

    assert composed.history == [instructions, question]


@pytest.mark.asyncio
async def test_compose_drops_a_block_whole_rather_than_keeping_its_notes_without_the_content():
    system = _message(MessageRole.SYSTEM, 10)
    question = _message(MessageRole.USER, 20)
    citation_rule = ChatMessage(role=MessageRole.SYSTEM, content="Cite by id.")
    attached_file = [_message(MessageRole.SYSTEM, 300), citation_rule]

    with _no_window():
        composed = await Conversation.compose_context_step(
            LLMWrappingAgent(),
            request=Conversation.compose([system, question], blocks=[attached_file]),
            conversation=_config(number_of_input_tokens=200),
        )

    assert composed.history == [system, question]


@pytest.mark.asyncio
async def test_compose_drops_an_earlier_turn_too_long_for_the_room_left():
    system = _message(MessageRole.SYSTEM, 10)
    oversized = _message(MessageRole.USER, 500)
    question = _message(MessageRole.USER, 20)

    with _no_window():
        composed = await Conversation.compose_context_step(
            LLMWrappingAgent(),
            request=Conversation.compose([system, oversized, question], blocks=[]),
            conversation=_config(number_of_input_tokens=200),
        )

    assert composed.history == [system, question]


@pytest.mark.asyncio
async def test_compose_shows_consecutive_turns_of_one_role_merged_as_the_model_receives_them():
    first, second = _message(MessageRole.USER, 5), _message(MessageRole.USER, 5)

    composed = await Conversation.compose_context_step(
        LLMWrappingAgent(),
        request=Conversation.compose([first, second], blocks=[]),
        conversation=_config(),
    )

    assert composed.history == merge_consecutive_messages([first, second])
    assert len(composed.history) == 1


@pytest.mark.asyncio
async def test_complete_generates_follow_ups_and_ends_with_the_given_stop_or_the_answer():
    answer = LLMEvent(output_messages=[Message.from_string(role="assistant", content="25 days")], chat_model_name="m")

    with patch(f"{CONVERSATION_MODULE}.generate_follow_up_questions", new=AsyncMock()) as follow_ups:
        default = await Conversation.complete_conversation_step(
            LLMWrappingAgent(),
            request=CompleteConversationEvent(answer=answer),
            conversation=_config(),
            displayer=MagicMock(),
            t=MagicMock(),
        )
        given = await Conversation.complete_conversation_step(
            LLMWrappingAgent(),
            request=Conversation.complete(answer=answer, stop=RAGSuccessStopEvent(answer="25 days")),
            conversation=_config(),
            displayer=MagicMock(),
            t=MagicMock(),
        )

    assert follow_ups.await_count == 2
    assert isinstance(default, LLMStopEvent)
    assert default.output_messages == answer.output_messages
    assert default.event_id != answer.event_id
    assert isinstance(given, RAGSuccessStopEvent)
