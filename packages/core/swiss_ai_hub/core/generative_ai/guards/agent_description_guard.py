import logging
from typing import Annotated

from llama_index.core import PromptTemplate
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.llms import LLM
from openai import NOT_GIVEN
from pydantic import Field, ValidationError

from swiss_ai_hub.core.generative_ai.guards.guard_result import GuardResult
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.i18n.locale_string import LocaleString

logger = logging.getLogger(__name__)


def guard_result_factory(t: LocaleHandler) -> type[GuardResult]:
    class LocalizedGuardResult(GuardResult):
        reasoning: Annotated[str, Field(description=t("lib.guards.agent_description_guard.reason"))]
        success: Annotated[bool, Field(description=t("lib.guards.agent_description_guard.success"))]

    LocalizedGuardResult.__doc__ = t("lib.guards.agent_description_guard.docstring")
    return LocalizedGuardResult


async def agent_description_guard(
    agent_description: LocaleString,
    llm: LLM,
    t: LocaleHandler,
    user_query: str,
    messages: list[ChatMessage],
) -> GuardResult:
    prompt = PromptTemplate(t("lib.guards.agent_description_guard.prompt"))
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

    llm_kwargs = {}

    if not llm.metadata.is_function_calling_model:
        llm_kwargs["tool_choice"] = NOT_GIVEN

    try:
        result = await llm.astructured_predict(
            guard_result_factory(t),
            prompt,
            llm_kwargs=llm_kwargs,
            agent_description=agent_description.in_locale(t.locale),
            user_query=user_query,
            history=history,
        )
        return GuardResult.model_validate(result)
    except (ValidationError, ValueError) as malformed_structured_output:
        # Flaky reasoning models can't always return parseable output; accept the request rather
        # than blocking the user on an unparseable suitability verdict.
        logger.warning("Agent-description guard failed (%s); accepting the request.", type(malformed_structured_output).__name__)
        return GuardResult(success=True, reasoning="Guard unavailable; accepting the request.")
