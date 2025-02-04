from typing import List

from llama_index.core import PromptTemplate
from llama_index.core.llms import LLM
from openai import NOT_GIVEN

from aihub_lib.generative_ai.guards.common.guard_result import GuardResult, guard_result_factory
from aihub_lib.generative_ai.prompting.few_shot.FewShotExample import FewShotExample
from aihub_lib.i18n.LocaleHandler import LocaleHandler


async def few_shot_guard(
    examples: List[FewShotExample],
    llm: LLM,
    t: LocaleHandler,
    user_query: str,
) -> GuardResult:
    prompt = PromptTemplate(t("lib.guards.few_shot_guard.prompt"))
    joined_examples = "".join(
        [
            PromptTemplate(t("lib.guards.common.user_message")).format(user=example.user.in_locale(t.locale))
            + PromptTemplate(t("lib.guards.common.agent_message")).format(agent=example.agent.in_locale(t.locale))
            for example in examples
        ]
    )

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
