"""`LLMEvent.for_hand_back` keeps the conversation an answer continues, within a byte budget.

The answer rides on every event that ends the turn. Carrying the prompt it was given made those events larger than the
broker accepts whenever an attached file was long in characters, such as a form of `____` blanks.
"""

from swiss_ai_hub.core.events.agent.semantic.llm.llm_event import HAND_BACK_BYTES, LLMEvent
from swiss_ai_hub.core.events.agent.semantic.llm.message import ImageContent, Message, TextContent

FORM = ("<tr><td>Name:</td><td>" + "_" * 180 + "</td></tr>\n") * 4300
ANSWER = [Message.from_string(role="assistant", content="Name, address and signature.", name="m")]


def _size(messages: list[Message]) -> int:
    return sum(len(message.model_dump_json().encode()) for message in messages)


def _answer(*inputs: Message) -> LLMEvent:
    return LLMEvent(input_messages=list(inputs), output_messages=ANSWER, chat_model_name="m", token_count_total=7)


def test_the_context_the_model_read_is_left_out():
    answer = _answer(
        Message.from_string(role="system", content="You answer about forms.\n" + FORM),
        Message.from_string(role="user", content="What is this?"),
        Message.from_string(role="assistant", content="A form."),
        Message(role="tool", contents=[TextContent(text="tool result")], tool_call_id="c1"),
        Message.from_string(role="user", content="Which fields?"),
    )

    handed_back = answer.for_hand_back()

    assert [(message.role, message.content) for message in handed_back.input_messages] == [
        ("user", "What is this?"),
        ("assistant", "A form."),
        ("user", "Which fields?"),
    ]
    assert handed_back.output_messages == answer.output_messages
    assert handed_back.event_id == answer.event_id
    assert handed_back.token_count_total == 7
    assert len(handed_back.model_dump_json(serialize_as_any=True).encode()) < HAND_BACK_BYTES


def test_a_short_conversation_is_kept_as_it_was():
    turns = [Message.from_string(role="user", content="Hi"), Message.from_string(role="assistant", content="Hello")]

    assert _answer(*turns, Message.from_string(role="user", content="Bye")).for_hand_back().input_messages == [
        *turns,
        Message.from_string(role="user", content="Bye"),
    ]


def test_the_newest_turns_are_kept_when_the_conversation_is_too_long():
    turns = [Message.from_string(role="user", content=f"{index:03d} " + "x" * 4000) for index in range(100)]

    kept = _answer(*turns).for_hand_back(max_bytes=50_000).input_messages

    assert kept == turns[-len(kept) :]
    assert 1 < len(kept) < len(turns)
    assert _size([*kept, *ANSWER]) <= 50_000


def test_a_question_too_long_alone_is_cut_and_marked():
    image = ImageContent(url="https://files.example/form.png")
    question = Message(role="user", contents=[TextContent(text="Fill this in: " + FORM), image])

    kept = _answer(Message.from_string(role="user", content="earlier"), question).for_hand_back().input_messages

    assert len(kept) == 1
    assert kept[0].content.startswith("Fill this in: ")
    assert kept[0].content.endswith("\n[…]")
    assert image in kept[0].contents
    assert _size([*kept, *ANSWER]) <= HAND_BACK_BYTES


def test_an_answer_without_input_hands_back_no_turns():
    assert LLMEvent(output_messages=ANSWER).for_hand_back().input_messages == []
