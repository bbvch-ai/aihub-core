import random
from typing import ClassVar

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import StartEvent, StopEvent

from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from playground.minimal_workflow.conditional_workflow.events.AboveThresholdEvent import AboveThresholdEvent
from playground.minimal_workflow.conditional_workflow.events.BelowThresholdEvent import BelowThresholdEvent


class ConditionalAgent(Agent):
    """Agent demonstrating conditional workflow branching."""

    name: ClassVar[LocaleString] = LocaleString(
        en="Conditional Agent", de="Bedingter Agent", fr="Agent Conditionnel", it="Agente Condizionale"
    )
    description: ClassVar[LocaleString] = LocaleString(
        en="Agent for conditional branching",
        de="Agent für bedingte Verzweigung",
        fr="Agent pour branchement conditionnel",
        it="Agente per branching condizionale",
    )
    icon: ClassVar[str] = "mage:arrowlist"

    @step()
    async def start_step(self, event: StartEvent) -> AboveThresholdEvent | BelowThresholdEvent:
        if random.random() > 0.5:
            print("[ConditionalAgent.start_step] Sent Event A")
            return AboveThresholdEvent()

        print("[ConditionalAgent.start_step] Sent Event B")
        return BelowThresholdEvent()

    @step()
    async def end_step(self, event: AboveThresholdEvent | BelowThresholdEvent) -> StopEvent:
        print(f"[ConditionalAgent.end_step] Received {event.event_name}")
        return StopEvent()
