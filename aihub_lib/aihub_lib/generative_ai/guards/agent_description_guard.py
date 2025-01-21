from typing import Type, List

from llama_index.core import PromptTemplate
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.llms import LLM
from pydantic import BaseModel, Field

from aihub_agent.displayers.EventDisplayer import EventDisplayer
from aihub_lib.i18n.LocaleHandler import LocaleHandler


class GuardResult(BaseModel):
    reasoning: str
    success: bool


def guard_result_factory(t: LocaleHandler) -> Type[GuardResult]:
    class LocalizedGuardResult(GuardResult):
        reasoning: str = Field(description=t("lib.guards.agent_description_guard.reasoning"))
        success: bool = Field(description=t("lib.guards.agent_description_guard.success"))

    LocalizedGuardResult.__doc__ = t("lib.guards.agent_description_guard.docstring")
    return LocalizedGuardResult


async def agent_description_guard(
        agent_description: str,
        llm_config: LLM,
        displayer: EventDisplayer,
        t: LocaleHandler,
        user_query: str,
        messages: List[ChatMessage],
) -> GuardResult:
    prompt = PromptTemplate(t("lib.guards.agent_description_guard"))
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
    async with llm_config.cost_reporting_llm(displayer) as llm:
        return llm.structured_predict(
            guard_result_factory(t), prompt, agent_description=agent_description, user_query=user_query, history=history
        )
