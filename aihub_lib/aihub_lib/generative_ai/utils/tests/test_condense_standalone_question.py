from unittest.mock import Mock

import pytest
from llama_index.core.base.llms.types import ChatMessage, ChatResponse, MessageRole

from aihub_lib.generative_ai.utils.condense_standalone_question import condense_standalone_question
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


def test_condense_preserves_multimodal_message(locale_handler, mock_llm):
    """Test that the original message with multimodal content is passed to LLM."""
    # Create a message with additional_kwargs simulating image content
    message = ChatMessage(
        role=MessageRole.USER,
        content="What is this?",
        additional_kwargs={"images": ["base64_encoded_image_data"]},
    )
    chat_history = []

    mock_llm.chat.return_value = ChatResponse(
        message=ChatMessage(role=MessageRole.ASSISTANT, content="What is the object shown in the image?")
    )

    result = condense_standalone_question(
        message=message,
        chat_history=chat_history,
        t=locale_handler,
        llm=mock_llm,
    )

    # Verify the original message (with additional_kwargs) was passed to llm.chat
    mock_llm.chat.assert_called_once()
    call_args = mock_llm.chat.call_args
    messages_passed = call_args.kwargs.get("messages") or call_args.args[0]

    # Second message should be the original user message with multimodal content
    assert messages_passed[1] == message
    assert messages_passed[1].additional_kwargs == {"images": ["base64_encoded_image_data"]}

    assert result.role == MessageRole.USER
    assert result.content == "What is the object shown in the image?"


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
