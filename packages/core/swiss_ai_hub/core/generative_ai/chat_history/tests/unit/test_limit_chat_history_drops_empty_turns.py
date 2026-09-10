from llama_index.core.base.llms.types import ChatMessage, MessageRole

from swiss_ai_hub.core.generative_ai.chat_history.limit_chat_history import limit_chat_history


def test_empty_content_turns_are_dropped():
    """A chat client can capture a streamed answer as an empty assistant message; forwarding it to the
    LLM makes most providers reject the request with a 400. Such turns must be dropped."""
    history = [
        ChatMessage(role=MessageRole.USER, content="what can you do?"),
        ChatMessage(role=MessageRole.ASSISTANT, content=""),
        ChatMessage(role=MessageRole.ASSISTANT, content="   "),
        ChatMessage(role=MessageRole.USER, content="what is the capital of France?"),
    ]

    limited = limit_chat_history(number_of_input_tokens=4096, chat_history=history)

    assert all(str(message.content or "").strip() for message in limited)
    assert [message.content for message in limited] == ["what can you do?", "what is the capital of France?"]
