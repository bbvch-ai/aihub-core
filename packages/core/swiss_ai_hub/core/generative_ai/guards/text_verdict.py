import logging
from typing import NamedTuple

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.llms import LLM

from swiss_ai_hub.core.generative_ai.resources.models.llm.reasoning_free_chat import ReasoningFreeChat

logger = logging.getLogger(__name__)

# Reasoning models on Infomaniak cannot reliably emit structured output (tool calls / JSON), but are
# reliable at a plain-text verdict token. Guards therefore ask for a token instead of a JSON object,
# with thinking off: a verdict is a trivial classification.


class BinaryVerdict(NamedTuple):
    success: bool
    reasoning: str


def binary_verdict_instruction(positive_token: str, negative_token: str) -> str:
    """Output-format instruction appended to a guard prompt to request a parseable text verdict."""
    return (
        f"\n\nRespond in plain text only (NOT JSON). On the FIRST line write exactly one word — "
        f"{positive_token} or {negative_token} — then on the next line give a brief reason."
    )


async def request_verdict(llm: LLM, prompt: str) -> str:
    """Ask the LLM for a plain-text response (reasoning disabled), returning its raw content."""
    return await request_verdict_for_messages(llm, [ChatMessage(role=MessageRole.USER, content=prompt)])


async def request_verdict_for_messages(llm: LLM, messages: list[ChatMessage]) -> str:
    """Plain-text verdict for a pre-built message list (e.g. a multimodal context prompt)."""
    response = await ReasoningFreeChat.achat(llm, messages)
    return str(response.message.content or "")


def parse_binary_verdict(text: str, positive_token: str, negative_token: str) -> BinaryVerdict | None:
    """Parse a ``TOKEN\\nreason`` response. The last token wins (so a label in the answer beats one in reasoning)."""
    upper = text.upper()
    positive_at, negative_at = upper.rfind(positive_token.upper()), upper.rfind(negative_token.upper())
    if positive_at == -1 and negative_at == -1:
        return None
    success = positive_at > negative_at
    chosen = positive_token if success else negative_token
    remainder = text[text.upper().find(chosen.upper()) + len(chosen) :]
    reasoning = remainder.strip(" \n\r\t:-").strip() or text.strip()
    return BinaryVerdict(success=success, reasoning=reasoning)
