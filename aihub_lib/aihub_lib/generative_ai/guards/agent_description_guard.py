from typing import Type

from llama_index.core import PromptTemplate
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


def agent_description_guard(
        agent_description: str, llm: LLM, displayer: EventDisplayer, t: LocaleHandler
) -> GuardResult:
    prompt = PromptTemplate(t("lib.guards.agent_description_guard"))
    async with llm.cost_reporting_llm(displayer) as llm:
        return llm.structured_predict(guard_result_factory(t), prompt, agent_description=agent_description)
