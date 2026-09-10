import logging

from llama_index.core import PromptTemplate
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.llms import LLM

from swiss_ai_hub.core.generative_ai.guards.guard_result import GuardResult
from swiss_ai_hub.core.generative_ai.guards.text_verdict import (
    binary_verdict_instruction,
    parse_binary_verdict,
    request_verdict,
)
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.i18n.locale_string import LocaleString

logger = logging.getLogger(__name__)

_ALLOW, _BLOCK = "ALLOW", "BLOCK"


async def agent_description_guard(
    agent_description: LocaleString,
    llm: LLM,
    t: LocaleHandler,
    user_query: str,
    messages: list[ChatMessage],
) -> GuardResult:
    history = "".join(
        [
            (
                PromptTemplate(t("lib.guards.agent_description_guard.user_message")).format(user=message.content)
                if message.role == MessageRole.USER
                else PromptTemplate(t("lib.guards.agent_description_guard.agent_message")).format(agent=message.content)
            )
            for message in messages
        ]
    )
    prompt = PromptTemplate(t("lib.guards.agent_description_guard.prompt")).format(
        agent_description=agent_description.in_locale(t.locale),
        user_query=user_query,
        history=history,
    ) + binary_verdict_instruction(_ALLOW, _BLOCK)

    verdict = parse_binary_verdict(await request_verdict(llm, prompt), _ALLOW, _BLOCK)
    if verdict is None:
        # Reasoning models occasionally return no recognizable verdict; accept rather than block the user.
        logger.warning("Agent-description guard returned no verdict; accepting the request.")
        return GuardResult(success=True, reasoning="Guard unavailable; accepting the request.")
    return GuardResult(success=verdict.success, reasoning=verdict.reasoning)
