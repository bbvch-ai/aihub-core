from typing import Type

from pydantic import BaseModel, Field

from aihub_lib.i18n.LocaleHandler import LocaleHandler


class GuardResult(BaseModel):
    reasoning: str
    success: bool


def guard_result_factory(t: LocaleHandler) -> Type[GuardResult]:
    class LocalizedGuardResult(GuardResult):
        reasoning: str = Field(description=t("lib.guards.agent_description_guard.reason"))
        success: bool = Field(description=t("lib.guards.agent_description_guard.success"))

    LocalizedGuardResult.__doc__ = t("lib.guards.agent_description_guard.docstring")
    return LocalizedGuardResult
