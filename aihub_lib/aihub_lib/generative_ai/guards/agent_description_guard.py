from typing import List

from llama_index.core import PromptTemplate
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.llms import LLM
from openai import NOT_GIVEN

from aihub_lib.generative_ai.guards.common.guard_result import GuardResult, guard_result_factory
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString


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
                PromptTemplate(t("lib.guards.common.user_message")).format(user=message.content)
                if message.role == MessageRole.USER
                else PromptTemplate(t("lib.guards.common.agent_message")).format(agent=message.content)
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
