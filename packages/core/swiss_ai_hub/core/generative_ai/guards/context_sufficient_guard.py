import logging
import re
from typing import Annotated

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.llms import LLM
from llama_index.core.prompts import RichPromptTemplate
from pydantic import Field

from swiss_ai_hub.core.generative_ai.guards.guard_result import GuardResult
from swiss_ai_hub.core.generative_ai.guards.text_verdict import request_verdict_for_messages
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler

logger = logging.getLogger(__name__)

# "INSUFFICIENT" contains "SUFFICIENT", so the positive token needs a negative lookbehind.
_INSUFFICIENT = re.compile(r"INSUFFICIENT")
_SUFFICIENT = re.compile(r"(?<!IN)SUFFICIENT")
_NEW_QUERY = re.compile(r"QUERY:\s*(.+)", re.IGNORECASE)
_VERDICT_WORD = re.compile(r"(?i)\b(?:in)?sufficient\b")


def _reasoning_from(text: str) -> str:
    """Drop the verdict token and the QUERY line, leaving the model's explanation."""
    without_query = _NEW_QUERY.sub("", text)
    without_verdict = _VERDICT_WORD.sub("", without_query, count=1)
    return without_verdict.strip(" \n\r\t:-.").strip() or text.strip()


class ContextGuardResult(GuardResult):
    """
    Specialized result for context sufficiency guards.

    Extends GuardResult with an additional field for new query suggestions
    when the current context is insufficient.
    """

    new_query: Annotated[
        str | None,
        Field(description="A revised query to get better search results if context was insufficient.", default=None),
    ]


def _verdict_instruction(more_hops_available: bool) -> str:
    instruction = (
        "\n\nRespond in plain text only (NOT JSON). On the FIRST line write exactly one word — "
        "SUFFICIENT (the context answers the question) or INSUFFICIENT — then on the next line a brief reason."
    )
    if more_hops_available:
        instruction += (
            " If INSUFFICIENT, add a final line beginning with 'QUERY:' followed by a single revised search query "
            "that follows the guidance above."
        )
    return instruction


def _parse(text: str, more_hops_available: bool) -> ContextGuardResult | None:
    last_insufficient = max((m.start() for m in _INSUFFICIENT.finditer(text.upper())), default=-1)
    last_sufficient = max((m.start() for m in _SUFFICIENT.finditer(text.upper())), default=-1)
    if last_insufficient == -1 and last_sufficient == -1:
        return None

    reasoning = _reasoning_from(text)
    if last_sufficient > last_insufficient:
        return ContextGuardResult(success=True, reasoning=reasoning)

    new_query_match = _NEW_QUERY.search(text)
    new_query = new_query_match.group(1).strip() if new_query_match else None
    # A hop needs a query; if the model gave none, treat the context as sufficient rather than retrieving on null.
    if more_hops_available and not new_query:
        return ContextGuardResult(success=True, reasoning=reasoning)
    return ContextGuardResult(success=False, reasoning=reasoning, new_query=new_query)


async def context_sufficient_guard(
    llm: LLM,
    t: LocaleHandler,
    user_query: str,
    context_message: ChatMessage | None,
    prev_queries: list[str],
    more_hops_available: bool,
    chat_history: list[ChatMessage],
) -> ContextGuardResult:
    sufficiency_prompt = RichPromptTemplate(t("lib.guards.context_sufficient_guard.prompt"))
    context_blocks = context_message.blocks if context_message is not None else []
    messages = sufficiency_prompt.format_messages(
        user_query=user_query,
        context_blocks=context_blocks,
        prev_queries="\n".join(prev_queries),
        chat_history=chat_history,
    )
    messages.append(ChatMessage(role=MessageRole.USER, content=_verdict_instruction(more_hops_available)))

    verdict = _parse(await request_verdict_for_messages(llm, messages), more_hops_available)
    if verdict is None:
        # Reasoning models occasionally return no recognizable verdict; treat context as sufficient
        # so the run answers with what it has instead of failing.
        logger.warning("Context-sufficiency guard returned no verdict; treating context as sufficient.")
        return ContextGuardResult(success=True, reasoning="Guard unavailable; treating context as sufficient.")
    return verdict
