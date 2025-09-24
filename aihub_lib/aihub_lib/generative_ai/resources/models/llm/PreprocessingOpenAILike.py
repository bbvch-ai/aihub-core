from collections.abc import Sequence
from typing import Any

from llama_index.core.base.llms.types import ChatMessage, ChatResponse, ChatResponseAsyncGen, ChatResponseGen
from llama_index.llms.openai_like import OpenAILike

from aihub_lib.generative_ai.resources.models.llm.message_preprocessor import merge_consecutive_messages


class PreprocessingOpenAILike(OpenAILike):
    """
    Extended OpenAILike that automatically preprocesses messages before sending to the model.

    This wrapper ensures all messages are cleaned and optimized for better model compatibility
    and performance by merging consecutive messages with the same role.
    """

    def _preprocess_messages(self, messages: Sequence[ChatMessage]) -> list[ChatMessage]:
        """Apply preprocessing to messages before sending to the model."""
        return merge_consecutive_messages(list(messages))

    def chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponse:
        """Chat with automatic message preprocessing."""
        preprocessed_messages = self._preprocess_messages(messages)
        return super().chat(preprocessed_messages, **kwargs)

    def stream_chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponseGen:
        """Stream chat with automatic message preprocessing."""
        preprocessed_messages = self._preprocess_messages(messages)
        return super().stream_chat(preprocessed_messages, **kwargs)

    async def achat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponse:
        """Async chat with automatic message preprocessing."""
        preprocessed_messages = self._preprocess_messages(messages)
        return await super().achat(preprocessed_messages, **kwargs)

    async def astream_chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponseAsyncGen:
        """Async stream chat with automatic message preprocessing."""
        preprocessed_messages = self._preprocess_messages(messages)
        return await super().astream_chat(preprocessed_messages, **kwargs)
