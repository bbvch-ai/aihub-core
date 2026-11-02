"""Chat messages nested two lists deep must survive the JetStream round trip.

`ComposeContextEvent.blocks` is a list of context blocks, each a list of chat messages. The event dumper used to
flatten one list level only, so the inner messages reached `json.dumps(default=str)` and came back as their
string form, which the receiving runner refused with a validation error.
"""

from llama_index.core.base.llms.types import ChatMessage, MessageRole

from swiss_ai_hub.core.events.agent import ComposeContextEvent


def test_nested_chat_message_blocks_round_trip_through_json():
    system = ChatMessage(role=MessageRole.SYSTEM, content="<user_context>likes tea</user_context>")
    user = ChatMessage(role=MessageRole.USER, content="What do I like?")
    event = ComposeContextEvent(history=[user], blocks=[[system], []])

    restored = ComposeContextEvent.deserialize_event(event.model_dump_json())

    assert restored.blocks == [[system], []]
    assert restored.history == [user]
