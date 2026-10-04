from collections.abc import Sequence
from typing import Any, ClassVar

from llama_index.core.base.llms.types import ChatMessage, ChatResponse
from llama_index.core.llms import LLM
from openai import BadRequestError


class ReasoningFreeChat:
    """A chat call with the model's thinking switched off, for steps whose answer is a label or a one-line rewrite
    (guards, classification, question condensing), where thinking only adds latency.

    Reasoning models read the switch from different chat-template keys, and ignore the one they do not know: some
    read ``enable_thinking`` (Qwen), others ``thinking`` (Kimi). Both are sent, so the switch reaches whichever
    reasoning model a profile picks. Models without a thinking mode ignore it, and Mistral-tokenizer models
    (Ministral) that reject ``chat_template_kwargs`` with a 400 get a plain request.
    """

    EXTRA_BODY: ClassVar[dict[str, Any]] = {"chat_template_kwargs": {"thinking": False, "enable_thinking": False}}

    @staticmethod
    async def achat(llm: LLM, messages: Sequence[ChatMessage]) -> ChatResponse:
        """``llm.achat`` with thinking off, or a plain call for a model that rejects the switch."""
        try:
            return await llm.achat(messages, extra_body=ReasoningFreeChat.EXTRA_BODY)
        except BadRequestError:
            return await llm.achat(messages)
