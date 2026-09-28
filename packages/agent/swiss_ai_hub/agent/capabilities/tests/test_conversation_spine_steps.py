"""The spine's steps on their own: the gate, the query, the join and the stop, without infrastructure."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent import (
    AnswerPostProcessedEvent,
    ContextBlockEvent,
    ConversationQueryEvent,
    LimitChatHistoryEvent,
    LLMEvent,
    LLMStopEvent,
    Message,
    NotAMetaQuestionEvent,
    StandaloneQuestionCondenserEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.testing.auth_utils import fake_user

from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent import LLMWrappingAgent
from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent_config import LLMWrappingAgentConfig
from swiss_ai_hub.agent.capabilities.conversation.conversation_capability import ConversationCapability
from swiss_ai_hub.agent.capabilities.conversation.conversation_preconditions import (
    all_context_blocks_reported,
    all_post_answer_hooks_reported,
    passed_meta_question_gate,
)

TOKEN_WORD = " hello"


def _config(*, condense: bool = False, number_of_input_tokens: int = 100_000) -> LLMWrappingAgentConfig:
    return LLMWrappingAgentConfig(
        agent_id="spine-test",
        name=LocaleString(en="Spine"),
        description=LocaleString(en="Spine fixture"),
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
async def test_the_gate_holds_a_chat_message_until_detection_clears_it():
    message = UserMessageEvent(user=fake_user(), messages=[ChatMessage(role=MessageRole.USER, content="hi")])
    assert await passed_meta_question_gate(user_message=message) is False
    assert await passed_meta_question_gate(user_message=message, clear=NotAMetaQuestionEvent(reasoning="")) is True
    assert await passed_meta_question_gate() is True, "a programmatic start has no message to clear"


@pytest.mark.asyncio
async def test_the_query_is_the_last_message_verbatim_unless_condensation_is_on():
    history = LimitChatHistoryEvent(
        limited_history=[
            ChatMessage(role=MessageRole.SYSTEM, content="be brief"),
            ChatMessage(role=MessageRole.USER, content="  what is the vacation policy? "),
        ]
    )
    events = await ConversationCapability.derive_query_step(
        LLMWrappingAgent(), history=history, conversation=_config(), displayer=MagicMock(), t=MagicMock()
    )

    assert [type(event) for event in events] == [ConversationQueryEvent]
    assert events[0].query == "  what is the vacation policy? "
    assert events[0].condensed is False


@pytest.mark.asyncio
async def test_condensation_emits_the_display_event_and_the_query_together():
    history = LimitChatHistoryEvent(limited_history=[ChatMessage(role=MessageRole.USER, content="and in 2027?")])
    condensed = ChatMessage(role=MessageRole.USER, content="What is the vacation policy in 2027?")
    reporting = MagicMock()
    reporting.__aenter__ = AsyncMock(return_value=MagicMock())
    reporting.__aexit__ = AsyncMock(return_value=False)

    with (
        patch.object(LLMConfig, "cost_reporting_llm", return_value=reporting),
        patch(
            "swiss_ai_hub.agent.capabilities.conversation.conversation_capability.condense_standalone_question",
            new=AsyncMock(return_value=condensed),
        ),
    ):
        events = await ConversationCapability.derive_query_step(
            LLMWrappingAgent(),
            history=history,
            conversation=_config(condense=True),
            displayer=MagicMock(display_thought=AsyncMock()),
            t=MagicMock(),
        )

    assert [type(event) for event in events] == [StandaloneQuestionCondenserEvent, ConversationQueryEvent]
    assert events[1].query == condensed.content
    assert events[1].condensed is True


@pytest.mark.asyncio
async def test_the_join_waits_for_one_block_per_installed_enricher():
    blocks = [ContextBlockEvent.empty("user_memory")]
    assert await all_context_blocks_reported(blueprint=LLMWrappingAgent, blocks=blocks) is False
    blocks.append(ContextBlockEvent.empty("organization_memory"))
    assert await all_context_blocks_reported(blueprint=LLMWrappingAgent, blocks=blocks) is True


@pytest.mark.asyncio
async def test_the_join_puts_blocks_behind_the_system_head_and_trims_them_first():
    system = _message(MessageRole.SYSTEM, 10)
    turn = _message(MessageRole.USER, 20)
    block = ContextBlockEvent(source="user_memory", messages=[_message(MessageRole.SYSTEM, 100)])

    with _no_window():
        enriched = await ConversationCapability.assemble_context_step(
            LLMWrappingAgent(),
            history=LimitChatHistoryEvent(limited_history=[system, turn]),
            conversation=_config(number_of_input_tokens=1_000),
            blocks=[block],
        )
        assert enriched.extended_history == [system, block.messages[0], turn]

        trimmed = await ConversationCapability.assemble_context_step(
            LLMWrappingAgent(),
            history=LimitChatHistoryEvent(limited_history=[system, turn]),
            conversation=_config(number_of_input_tokens=60),
            blocks=[block],
        )
        assert trimmed.extended_history == [system, turn], "the block gives way, never the turn or the head"


@pytest.mark.asyncio
async def test_the_join_passes_the_history_through_when_no_block_has_content():
    history = [_message(MessageRole.USER, 5)]
    enriched = await ConversationCapability.assemble_context_step(
        LLMWrappingAgent(),
        history=LimitChatHistoryEvent(limited_history=history),
        conversation=_config(),
        blocks=[ContextBlockEvent.empty("user_memory"), ContextBlockEvent.empty("organization_memory")],
    )
    assert enriched.extended_history == history


@pytest.mark.asyncio
async def test_the_stop_waits_for_every_post_answer_hook_then_carries_the_answer():
    assert await all_post_answer_hooks_reported(blueprint=LLMWrappingAgent) is False
    hooks = [AnswerPostProcessedEvent(source="user_memory")]
    assert await all_post_answer_hooks_reported(blueprint=LLMWrappingAgent, hooks=hooks) is True

    answer = LLMEvent(output_messages=[Message.from_string(role="assistant", content="25 days")], chat_model_name="m")
    with patch(
        "swiss_ai_hub.agent.capabilities.conversation.conversation_capability.generate_follow_up_questions",
        new=AsyncMock(),
    ) as follow_ups:
        stop = await ConversationCapability.stop_step(
            LLMWrappingAgent(), llm_event=answer, conversation=_config(), displayer=MagicMock(), t=MagicMock()
        )

    assert isinstance(stop, LLMStopEvent)
    assert stop.output_messages == answer.output_messages
    assert stop.event_id != answer.event_id
    follow_ups.assert_awaited_once()
