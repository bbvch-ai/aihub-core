from typing import Annotated

from llama_index.core import PromptTemplate
from llama_index.core.llms import LLM
from openai import NOT_GIVEN
from pydantic import BaseModel, Field

from aihub_lib.i18n.LocaleHandler import LocaleHandler


class SensitiveInfoGuardResult(BaseModel):
    reasoning: Annotated[str, Field(description="The reasoning behind whether sensitive information is present.")]
    success: Annotated[
        bool,
        Field(description="True if no sensitive information was found, false if sensitive information was detected."),
    ]
    cleaned_answer: Annotated[
        str | None,
        Field(description="The revised response with sensitive information removed, if applicable.", default=None),
    ]


def sensitive_info_guard_result_factory(t: LocaleHandler) -> type[SensitiveInfoGuardResult]:
    class LocalizedSensitiveInfoGuardResult(SensitiveInfoGuardResult):
        reasoning: Annotated[str, Field(description=t("lib.guards.sensitive_info_guard.reason"))]
        success: Annotated[bool, Field(description=t("lib.guards.sensitive_info_guard.success"))]
        cleaned_answer: Annotated[str | None, Field(description=t("lib.guards.sensitive_info_guard.cleaned_answer"))]

    LocalizedSensitiveInfoGuardResult.__doc__ = t("lib.guards.sensitive_info_guard.docstring")
    return LocalizedSensitiveInfoGuardResult


async def sensitive_info_guard(
    llm: LLM,
    t: LocaleHandler,
    answer: str,
) -> SensitiveInfoGuardResult:
    """
    Guard that checks if the response contains sensitive information and cleans it if necessary.
    """
    prompt = PromptTemplate(t("lib.guards.sensitive_info_guard.prompt"))

    llm_kwargs = {}
    if not llm.metadata.is_function_calling_model:
        llm_kwargs["tool_choice"] = NOT_GIVEN

    result = llm.structured_predict(
        sensitive_info_guard_result_factory(t),
        prompt,
        llm_kwargs=llm_kwargs,
        answer=answer,
    )

    guard_result = SensitiveInfoGuardResult.model_validate(result)

    # For sensitive info guard, success=False means sensitive info was found and needs cleaning
    # success=True means no sensitive info was detected
    return guard_result
