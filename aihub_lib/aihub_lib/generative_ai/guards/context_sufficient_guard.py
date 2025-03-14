from typing import Optional, Type

from llama_index.core import PromptTemplate
from llama_index.core.llms import LLM
from openai import NOT_GIVEN
from pydantic import BaseModel, Field

from aihub_lib.i18n.LocaleHandler import LocaleHandler


class ContextGuardResult(BaseModel):
    reasoning: str
    success: bool
    new_query: Optional[str] = None


def context_guard_result_factory(t: LocaleHandler) -> Type[ContextGuardResult]:
    class LocalizedContextGuardResult(ContextGuardResult):
        reasoning: str = Field(description=t("lib.guards.context_sufficient_guard.reason"))
        success: bool = Field(description=t("lib.guards.context_sufficient_guard.success"))
        new_query: Optional[str] = Field(default=None, description=t("lib.guards.context_sufficient_guard.new_query"))

    LocalizedContextGuardResult.__doc__ = t("lib.guards.context_sufficient_guard.docstring")
    return LocalizedContextGuardResult


async def context_sufficient_guard(
    llm: LLM,
    t: LocaleHandler,
    user_query: str,
    context: str,
) -> ContextGuardResult:
    sufficiency_prompt = PromptTemplate(t("lib.guards.context_sufficient_guard.message"))

    llm_kwargs = {}
    if not llm.metadata.is_function_calling_model:
        llm_kwargs["tool_choice"] = NOT_GIVEN

    result = llm.structured_predict(
        context_guard_result_factory(t),
        sufficiency_prompt,
        llm_kwargs=llm_kwargs,
        user_query=user_query,
        context=context,
    )

    guard_result = ContextGuardResult.model_validate(result)

    return guard_result
