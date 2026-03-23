from typing import Annotated

from llama_index.core import PromptTemplate
from llama_index.core.llms import LLM
from openai import NOT_GIVEN
from pydantic import Field

from swiss_ai_hub.core.generative_ai.guards.guard_result import GuardResult
from swiss_ai_hub.core.generative_ai.prompting.few_shot.few_shot_guard_example import FewShotGuardExample
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler


def guard_result_factory(t: LocaleHandler) -> type[GuardResult]:
    class LocalizedGuardResult(GuardResult):
        reasoning: Annotated[str, Field(description=t("lib.guards.few_shot_guard.reason"))]
        success: Annotated[bool, Field(description=t("lib.guards.few_shot_guard.success"))]

    LocalizedGuardResult.__doc__ = t("lib.guards.few_shot_guard.docstring")
    return LocalizedGuardResult


async def few_shot_guard(
    examples: list[FewShotGuardExample],
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
