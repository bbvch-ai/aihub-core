"""A tool loop that outgrew the prompt is condensed before the model decides again: earlier results first, each
keeping its place, then the conversation before the request, and only as a last resort dropping old results. The
request and the latest round of results are never touched."""

from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    Message,
    TextContent,
    ToolLoopCondensedEvent,
    ToolLoopIterationEvent,
    ToolLoopMode,
    ToolLoopState,
)

from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop import fits_the_prompt, outgrew_the_prompt
from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop_condenser import ToolLoopCondenser
from swiss_ai_hub.agent.i18n.agent_locale_handler import AgentLocaleHandler

T = AgentLocaleHandler("en")


def _counter(text: str) -> list[str]:
    return text.split()


def _llm(summary: str = "short") -> MagicMock:
    @asynccontextmanager
    async def cost_reporting_llm(*_args: Any, **_kwargs: Any):
        yield MagicMock(achat=AsyncMock(return_value=MagicMock(message=MagicMock(content=summary))))

    llm = MagicMock()
    llm.cost_reporting_llm = cost_reporting_llm
    llm.token_counter = _counter
    return llm


def _calling(*tool_call_ids: str) -> Message:
    return Message(
        role="assistant",
        contents=[],
        tool_calls=[
            {"id": tool_call_id, "type": "function", "function": {"name": "search", "arguments": "{}"}}
            for tool_call_id in tool_call_ids
        ],
    )


def _result(tool_call_id: str, words: int) -> Message:
    return Message(
        role="tool", tool_call_id=tool_call_id, name="search", contents=[TextContent(text=" ".join(["fact"] * words))]
    )


def _conversation(earlier_words: int = 0) -> list[Message]:
    earlier = (
        [
            Message.from_string(role="user", content=" ".join(["earlier"] * earlier_words)),
            Message.from_string(role="assistant", content="earlier answer"),
        ]
        if earlier_words
        else []
    )
    return [
        Message.from_string(role="system", content="You are helpful."),
        *earlier,
        Message.from_string(role="user", content="What changed in Q1?"),
        _calling("c1"),
        _result("c1", 400),
        _calling("c2"),
        _result("c2", 50),
    ]


def _state(messages: list[Message]) -> ToolLoopState:
    return ToolLoopState(messages=messages, mode=ToolLoopMode.ANSWER, needs_condensing=True)


async def _condense(messages: list[Message], budget: int, summary: str = "short") -> tuple[ToolLoopState, MagicMock]:
    displayer = MagicMock(spec=EventDisplayer, display_event=AsyncMock())
    condenser = ToolLoopCondenser(_llm(summary), budget, displayer, T, user=None)
    return await condenser.condense(_state(messages)), displayer


@pytest.mark.asyncio
async def test_earlier_results_are_condensed_in_place_and_the_latest_round_kept():
    state, displayer = await _condense(_conversation(), budget=200)

    contents = [message.content for message in state.messages]
    assert contents[3] == "[Condensed earlier result] short"
    assert state.messages[3].tool_call_id == "c1"
    assert contents[5] == " ".join(["fact"] * 50)
    assert not state.needs_condensing
    event = displayer.display_event.await_args.args[0]
    assert isinstance(event, ToolLoopCondensedEvent)
    assert (event.condensed_results, event.condensed_turns) == (1, 0)
    assert event.tokens_after < event.tokens_before


@pytest.mark.asyncio
async def test_the_conversation_before_the_request_becomes_one_summary_when_results_are_not_enough():
    state, displayer = await _condense(_conversation(earlier_words=400), budget=200)

    roles = [message.role for message in state.messages]
    assert roles[:3] == ["system", "system", "user"]
    assert state.messages[1].content.startswith("Summary of the earlier conversation:")
    assert state.messages[2].content == "What changed in Q1?"
    assert displayer.display_event.await_args.args[0].condensed_turns == 2


@pytest.mark.asyncio
async def test_old_results_are_dropped_only_when_condensing_cannot_make_room():
    state, _ = await _condense(_conversation(), budget=120, summary=" ".join(["long"] * 300))

    assert "removed to fit the context" in state.messages[3].content
    assert state.messages[5].content == " ".join(["fact"] * 50)


def test_a_conversation_outgrows_the_prompt_by_its_size():
    assert ToolLoopCondenser.outgrown(_conversation(), [], 200, _counter)
    assert not ToolLoopCondenser.outgrown(_conversation(), [], 10_000, _counter)


@pytest.mark.asyncio
async def test_condensing_and_deciding_never_both_take_an_iteration():
    over = ToolLoopIterationEvent(state=_state(_conversation()))
    fitted = ToolLoopIterationEvent(state=_state(_conversation()).model_copy(update={"needs_condensing": False}))

    assert (await outgrew_the_prompt(over), await fits_the_prompt(over)) == (True, False)
    assert (await outgrew_the_prompt(fitted), await fits_the_prompt(fitted)) == (False, True)


@pytest.mark.asyncio
async def test_a_latest_round_that_alone_outgrows_the_prompt_is_cut_to_fit():
    messages = [
        Message.from_string(role="system", content="You are helpful."),
        Message.from_string(role="user", content="What changed in Q1?"),
        _calling("c1"),
        _result("c1", 400),
    ]

    state, displayer = await _condense(messages, budget=200)

    assert "cut to fit the context" in state.messages[3].content
    assert not ToolLoopCondenser.outgrown(state.messages, [], 220, _counter)
    assert displayer.display_event.await_args.args[0].tokens_after <= 200


@pytest.mark.asyncio
async def test_nothing_is_announced_when_nothing_could_be_condensed():
    messages = [Message.from_string(role="system", content=" ".join(["rules"] * 300))]

    state, displayer = await _condense(messages, budget=100)

    displayer.display_event.assert_not_awaited()
    assert state.messages == messages
