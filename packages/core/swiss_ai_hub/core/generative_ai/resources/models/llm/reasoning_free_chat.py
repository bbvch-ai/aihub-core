from collections.abc import Sequence
from typing import Any, ClassVar

from llama_index.core.base.llms.types import ChatMessage, ChatResponse
from llama_index.core.llms import LLM
from openai import BadRequestError


class ReasoningFreeChat:
    """A chat call with the model's thinking switched off, for steps whose answer is a label or a one-line rewrite
    (guards, classification, question condensing), where thinking only adds latency.

    Model families read different keys: Qwen3 honours only ``enable_thinking`` and keeps thinking under
    ``thinking`` alone, often until it runs out of output tokens without an answer; other vLLM templates honour
    ``thinking``. Both are sent. Mistral-tokenizer models (Ministral) reject ``chat_template_kwargs`` with a 400
    and have no thinking to switch off, so they get a plain request.
    """

    EXTRA_BODY: ClassVar[dict[str, Any]] = {"chat_template_kwargs": {"thinking": False, "enable_thinking": False}}

    @staticmethod
    async def achat(llm: LLM, messages: Sequence[ChatMessage]) -> ChatResponse:
        """``llm.achat`` with thinking off, or a plain call for a model that rejects the switch."""
        try:
            return await llm.achat(messages, extra_body=ReasoningFreeChat.EXTRA_BODY)
        except BadRequestError:
            return await llm.achat(messages)
