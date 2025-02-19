from typing import List, Type

from llama_index.core import PromptTemplate
from llama_index.core.llms import LLM
from openai import NOT_GIVEN
from pydantic import BaseModel, Field

from aihub_lib.generative_ai.prompting.few_shot.FewShotGuardExample import FewShotGuardExample
from aihub_lib.i18n.LocaleHandler import LocaleHandler


class GuardResult(BaseModel):
    reasoning: str
    success: bool


def guard_result_factory(t: LocaleHandler) -> Type[GuardResult]:
    class LocalizedGuardResult(GuardResult):
        reasoning: str = Field(description=t("lib.guards.few_shot_guard.reason"))
        success: bool = Field(description=t("lib.guards.few_shot_guard.success"))

    LocalizedGuardResult.__doc__ = t("lib.guards.few_shot_guard.docstring")
    return LocalizedGuardResult


async def few_shot_guard(
    examples: List[FewShotGuardExample],
    llm: LLM,
    t: LocaleHandler,
    user_query: str,
) -> GuardResult:
    prompt = PromptTemplate(t("lib.guards.few_shot_guard.prompt"))

    user_template = PromptTemplate(t("lib.guards.few_shot_guard.user_message"))
    success_template = PromptTemplate(t("lib.guards.few_shot_guard.success_message"))
    reason_template = PromptTemplate(t("lib.guards.few_shot_guard.reason_message"))

    def format_example(example):
        return "".join(
            [
                user_template.format(user=example.user.in_locale(t.locale)),
                success_template.format(success=example.success),
                reason_template.format(reason=example.reason.in_locale(t.locale)),
            ]
        )

    joined_examples = "".join(format_example(example) for example in examples)

    llm_kwargs = {}
    if not llm.metadata.is_function_calling_model:
        llm_kwargs["tool_choice"] = NOT_GIVEN

    result = llm.structured_predict(
        guard_result_factory(t),
        prompt,
        llm_kwargs=llm_kwargs,
        examples=joined_examples,
        user_query=user_query,
    )

    return GuardResult.model_validate(result)
