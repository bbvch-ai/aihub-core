from unittest.mock import Mock

import pytest
from llama_index.core.base.llms.types import ChatMessage, ChatResponse, ImageBlock, MessageRole, TextBlock

from aihub_lib.generative_ai.retrieval.condense_standalone_question import condense_standalone_question
from aihub_lib.i18n.LocaleHandler import LocaleHandler


@pytest.fixture
def locale_handler():
    return LocaleHandler(locale="en")


@pytest.fixture
def mock_llm():
    llm = Mock()
    return llm


def test_condense_text_only_message(locale_handler, mock_llm):
    """Test condensing a simple text-only user message."""
    message = ChatMessage(role=MessageRole.USER, content="What is this?")
    chat_history = [
        ChatMessage(role=MessageRole.USER, content="Tell me about Python"),
        ChatMessage(role=MessageRole.ASSISTANT, content="Python is a programming language."),
    ]

    mock_llm.chat.return_value = ChatResponse(
        message=ChatMessage(role=MessageRole.ASSISTANT, content="What is Python?")
    )

    result = condense_standalone_question(
        message=message,
        chat_history=chat_history,
        t=locale_handler,
        llm=mock_llm,
    )

    assert result.role == MessageRole.USER
    assert result.content == "What is Python?"
    mock_llm.chat.assert_called_once()


def test_condense_filters_system_messages(locale_handler, mock_llm):
    """Test that system messages are filtered out from chat history."""
    message = ChatMessage(role=MessageRole.USER, content="Tell me more")
    chat_history = [
        ChatMessage(role=MessageRole.SYSTEM, content="You are a helpful assistant"),
        ChatMessage(role=MessageRole.USER, content="What is AI?"),
        ChatMessage(role=MessageRole.ASSISTANT, content="AI stands for Artificial Intelligence."),
    ]

    mock_llm.chat.return_value = ChatResponse(
        message=ChatMessage(role=MessageRole.ASSISTANT, content="Tell me more about Artificial Intelligence")
    )

    result = condense_standalone_question(
        message=message,
        chat_history=chat_history,
        t=locale_handler,
        llm=mock_llm,
    )

    # Verify the LLM was called
    mock_llm.chat.assert_called_once()
    call_args = mock_llm.chat.call_args

    # The messages passed to llm.chat should be [system_instruction, user_message]
    messages_passed = call_args.kwargs.get("messages") or call_args.args[0]
    assert len(messages_passed) == 2
    assert messages_passed[0].role == MessageRole.SYSTEM
    assert messages_passed[1].role == MessageRole.USER

    assert result.role == MessageRole.USER
    assert result.content == "Tell me more about Artificial Intelligence"


def test_condense_preserves_multimodal_message_with_image_blocks(locale_handler, mock_llm):
    """Test that the original message with image blocks is passed to LLM for multimodal processing."""
    # Create a message with both text and image blocks (multimodal content)
    message = ChatMessage(
        role=MessageRole.USER,
        blocks=[
            TextBlock(text="What is this?"),
            ImageBlock(
                url="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
            ),
        ],
    )
    chat_history = []

    mock_llm.chat.return_value = ChatResponse(
        message=ChatMessage(role=MessageRole.ASSISTANT, content="What is the red apple shown in the image?")
    )

    result = condense_standalone_question(
        message=message,
        chat_history=chat_history,
        t=locale_handler,
        llm=mock_llm,
    )

    # Verify the original multimodal message was passed to llm.chat
    mock_llm.chat.assert_called_once()
    call_args = mock_llm.chat.call_args
    messages_passed = call_args.kwargs.get("messages") or call_args.args[0]

    # Second message should be the original user message with image blocks preserved
    assert messages_passed[1] == message
    assert len(messages_passed[1].blocks) == 2
    assert isinstance(messages_passed[1].blocks[0], TextBlock)
    assert isinstance(messages_passed[1].blocks[1], ImageBlock)

    assert result.role == MessageRole.USER
    assert result.content == "What is the red apple shown in the image?"


def test_condense_with_empty_chat_history(locale_handler, mock_llm):
    """Test condensing when chat history is empty."""
    message = ChatMessage(role=MessageRole.USER, content="Hello world")
    chat_history = []

    mock_llm.chat.return_value = ChatResponse(message=ChatMessage(role=MessageRole.ASSISTANT, content="Hello world"))

    result = condense_standalone_question(
        message=message,
        chat_history=chat_history,
        t=locale_handler,
        llm=mock_llm,
    )

    assert result.role == MessageRole.USER
    assert result.content == "Hello world"
    mock_llm.chat.assert_called_once()


def test_condense_returns_user_role_message(locale_handler, mock_llm):
    """Test that the returned message always has USER role regardless of LLM response."""
    message = ChatMessage(role=MessageRole.USER, content="What about that?")
    chat_history = [
        ChatMessage(role=MessageRole.USER, content="Tell me about cats"),
        ChatMessage(role=MessageRole.ASSISTANT, content="Cats are feline animals."),
    ]

    # LLM returns ASSISTANT role, but function should convert to USER
    mock_llm.chat.return_value = ChatResponse(
        message=ChatMessage(role=MessageRole.ASSISTANT, content="What are the characteristics of cats?")
    )

    result = condense_standalone_question(
        message=message,
        chat_history=chat_history,
        t=locale_handler,
        llm=mock_llm,
    )

    # Result should always be USER role
    assert result.role == MessageRole.USER
    assert result.content == "What are the characteristics of cats?"
