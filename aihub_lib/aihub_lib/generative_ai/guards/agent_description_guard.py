from typing import List, Type

from llama_index.core import PromptTemplate
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.llms import LLM
from llama_index.llms.openai_like import OpenAILike
from openai import NOT_GIVEN
from pydantic import BaseModel, Field

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString


class GuardResult(BaseModel):
    reasoning: str
    success: bool


def guard_result_factory(t: LocaleHandler) -> Type[GuardResult]:
    class LocalizedGuardResult(GuardResult):
        reasoning: str = Field(description=t("lib.guards.agent_description_guard.reason"))
        success: bool = Field(description=t("lib.guards.agent_description_guard.success"))

    LocalizedGuardResult.__doc__ = t("lib.guards.agent_description_guard.docstring")
    return LocalizedGuardResult


async def agent_description_guard(
    agent_description: LocaleString,
    llm: LLM,
    t: LocaleHandler,
    user_query: str,
    messages: List[ChatMessage],
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

    result = llm.structured_predict(
        guard_result_factory(t),
        prompt,
        llm_kwargs=llm_kwargs,
        agent_description=agent_description.in_locale(t.locale),
        user_query=user_query,
        history=history,
    )

    return GuardResult.model_validate(result)
