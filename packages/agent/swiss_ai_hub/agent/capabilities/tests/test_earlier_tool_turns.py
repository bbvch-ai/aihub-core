"""A later turn sees what the tools returned for the earlier answers, which chat clients send back as text only."""

from typing import Any

import pytest
from swiss_ai_hub.core.events.agent import Message

from swiss_ai_hub.agent.capabilities.tool_loop.earlier_tool_turns import EarlierToolTurns


class _ThreadContext:
    def __init__(self) -> None:
        self.values: dict[str, Any] = {}

    async def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    async def set(self, key: str, value: Any) -> None:
        self.values[key] = value


SYSTEM = Message.from_string(role="system", content="Use your tools.")
QUESTION = Message.from_string(role="user", content="Which region grew most?")
CALL = Message(
    role="assistant",
    contents=[],
    tool_calls=[{"id": "c1", "type": "function", "function": {"name": "read_attached_files", "arguments": "{}"}}],
)
RESULT = Message.from_string(role="tool", content="Growth is in percent with one decimal.").model_copy(
    update={"tool_call_id": "c1", "name": "read_attached_files"}
)
ANSWER = Message.from_string(role="assistant", content="East grew most.")
FOLLOW_UP = Message.from_string(role="user", content="How should growth be rounded?")


async def _kept_after_first_turn() -> _ThreadContext:
    thread_context = _ThreadContext()
    await EarlierToolTurns(thread_context, "tools").keep([SYSTEM, QUESTION, CALL, RESULT])
    return thread_context


@pytest.mark.asyncio
async def test_an_earlier_answer_gets_its_tool_calls_and_results_back_on_the_next_turn():
    thread_context = await _kept_after_first_turn()

    restored = await EarlierToolTurns(thread_context, "tools").restore([SYSTEM, QUESTION, ANSWER, FOLLOW_UP])

    assert [(message.role, message.content) for message in restored] == [
        ("system", "Use your tools."),
        ("user", "Which region grew most?"),
        ("assistant", ""),
        ("tool", "Growth is in percent with one decimal."),
        ("assistant", "East grew most."),
        ("user", "How should growth be rounded?"),
    ]
    assert restored[2].tool_calls == CALL.tool_calls
    assert restored[3].tool_call_id == "c1"


@pytest.mark.asyncio
async def test_a_conversation_without_kept_turns_is_left_as_it_is():
    restored = await EarlierToolTurns(_ThreadContext(), "tools").restore([SYSTEM, QUESTION, ANSWER, FOLLOW_UP])

    assert restored == [SYSTEM, QUESTION, ANSWER, FOLLOW_UP]


@pytest.mark.asyncio
async def test_only_the_last_question_s_calls_are_kept_not_the_restored_ones():
    thread_context = await _kept_after_first_turn()
    second_call = CALL.model_copy(update={"tool_calls": [{**CALL.tool_calls[0], "id": "c2"}]})
    second_result = RESULT.model_copy(update={"tool_call_id": "c2"})

    await EarlierToolTurns(thread_context, "tools").keep(
        [SYSTEM, QUESTION, CALL, RESULT, ANSWER, FOLLOW_UP, second_call, second_result]
    )

    kept = thread_context.values["tool_loop:tools:earlier_turns"]
    assert list(kept) == ["Which region grew most?", "How should growth be rounded?"]
    assert [message["tool_call_id"] for message in kept["How should growth be rounded?"]] == [None, "c2"]


@pytest.mark.asyncio
async def test_an_answer_without_tool_calls_keeps_nothing():
    thread_context = _ThreadContext()

    await EarlierToolTurns(thread_context, "tools").keep([SYSTEM, QUESTION])

    assert thread_context.values == {}


@pytest.mark.asyncio
async def test_only_the_latest_turns_are_kept():
    thread_context = _ThreadContext()
    for number in range(EarlierToolTurns.KEPT_TURNS + 2):
        question = Message.from_string(role="user", content=f"Question {number}")
        await EarlierToolTurns(thread_context, "tools").keep([question, CALL, RESULT])

    kept = thread_context.values["tool_loop:tools:earlier_turns"]
    assert list(kept) == [f"Question {number}" for number in range(2, EarlierToolTurns.KEPT_TURNS + 2)]
