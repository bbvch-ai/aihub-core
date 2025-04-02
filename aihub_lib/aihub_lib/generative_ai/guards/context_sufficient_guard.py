from typing import Type

from llama_index.core import PromptTemplate
from llama_index.core.llms import LLM
from openai import NOT_GIVEN
from pydantic import BaseModel, Field

from aihub_lib.i18n.LocaleHandler import LocaleHandler


class GuardResult(BaseModel):
    reasoning: str
    success: bool


def guard_result_factory(t: LocaleHandler) -> Type[GuardResult]:
    class LocalizedGuardResult(GuardResult):
        reasoning: str = Field(description=t("lib.guards.context_sufficient_guard.reason"))
        success: bool = Field(description=t("lib.guards.context_sufficient_guard.success"))

    LocalizedGuardResult.__doc__ = t("lib.guards.context_sufficient_guard.docstring")
    return LocalizedGuardResult


async def context_sufficient_guard(llm: LLM, t: LocaleHandler, user_query: str, context: str) -> GuardResult:
    prompt = PromptTemplate(t("lib.guards.context_sufficient_guard.prompt"))

    llm_kwargs = {}
    if not llm.metadata.is_function_calling_model:
        llm_kwargs["tool_choice"] = NOT_GIVEN

    result = llm.structured_predict(
        guard_result_factory(t), prompt, llm_kwargs=llm_kwargs, user_query=user_query, context=context
    )

    return GuardResult.model_validate(result)
