from typing import ClassVar

from swiss_ai_hub.core.events.agent import StartEvent, StopEvent
from swiss_ai_hub.core.i18n import LocaleString

from playground.minimal_workflow.multistep_human_in_the_loop_workflow.events.first_step_human_in_the_loop import (
    FirstStepHumanInTheLoop,
)
from playground.minimal_workflow.multistep_human_in_the_loop_workflow.events.second_step_human_in_the_loop import (
    SecondStepHumanInTheLoop,
)
from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.workflow.decorators.step import step


class MultistepHumanInTheLoopAgent(Agent):
    """Agent demonstrating multi-step human-in-the-loop patterns."""

    name: ClassVar[LocaleString] = LocaleString(
        en="Multistep HITL Agent",
        de="Mehrstufiger HITL Agent",
        fr="Agent HITL Multi-étapes",
        it="Agente HITL Multistep",
    )
    description: ClassVar[LocaleString] = LocaleString(
        en="Agent for multistep HITL demo",
        de="Agent für mehrstufige HITL Demo",
        fr="Agent pour démo HITL multi-étapes",
        it="Agente per demo HITL multistep",
    )
    icon: ClassVar[str] = "mage:user-plus"

    @step()
    async def start_step(self, event: StartEvent) -> FirstStepHumanInTheLoop.request:
        print("[MultistepHumanInTheLoopAgent.start_step]")
        return FirstStepHumanInTheLoop.invoke(question="Shall I continue?")

    @step()
    async def second_hitl(self, event: FirstStepHumanInTheLoop.response) -> SecondStepHumanInTheLoop.request:
        print(
            "[FirstStepHumanInTheLoop.second_hitl]",
            event.request_event.question,
            event.response,
        )
        return SecondStepHumanInTheLoop.invoke(question="Are you sure?")

    @step()
    async def end_step(self, event: SecondStepHumanInTheLoop.response) -> StopEvent:
        print(
            "[MultistepHumanInTheLoopAgent.end_step]",
            event.request_event.question,
            event.response,
        )
        return StopEvent()
