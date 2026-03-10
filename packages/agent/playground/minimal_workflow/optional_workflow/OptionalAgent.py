import random
from typing import ClassVar

from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.nats.events.control.start.StartEvent import StartEvent
from swiss_ai_hub.core.nats.events.control.stop.StopEvent import StopEvent

from playground.minimal_workflow.optional_workflow.events.EventOptionalA import EventOptionalA
from playground.minimal_workflow.optional_workflow.events.EventOptionalB import EventOptionalB
from playground.minimal_workflow.optional_workflow.events.EventOptionalC import EventOptionalC
from playground.minimal_workflow.optional_workflow.events.EventOptionalD import EventOptionalD
from swiss_ai_hub.agent.agents.Agent import Agent
from swiss_ai_hub.agent.workflow.decorators.step import step


class OptionalAgent(Agent):
    """Agent demonstrating optional event patterns."""

    name: ClassVar[LocaleString] = LocaleString(
        en="Optional Agent", de="Optionaler Agent", fr="Agent Optionnel", it="Agente Opzionale"
    )
    description: ClassVar[LocaleString] = LocaleString(
        en="Agent for optional event demo",
        de="Agent für optionales Event Demo",
        fr="Agent pour démo événement optionnel",
        it="Agente per demo evento opzionale",
    )
    icon: ClassVar[str] = "mage:question-mark-circle"

    @step()
    async def start_step(self, event: StartEvent) -> list[EventOptionalA | EventOptionalB]:
        if random.random() > 0.5:
            print("[OptionalAgent.start_step] Only EventA")
            return [EventOptionalA()]
        print("[OptionalAgent.start_step] EventA & EventB")
        return [EventOptionalB(), EventOptionalA()]

    @step(max_executions_per_run=1)
    async def optional_step(
        self, event: EventOptionalA, optional_event: EventOptionalB | None
    ) -> EventOptionalC | EventOptionalD:
        if optional_event:
            print("[OptionalAgent.optional_step] Received Optional EventB")
            return EventOptionalC()
        print("[OptionalAgent.optional_step] Did not receive Optional EventB")
        return EventOptionalD()

    @step(max_executions_per_run=1)
    async def end_step(self, event: EventOptionalC | EventOptionalD) -> StopEvent:
        print(f"[OptionalAgent.end_step] Received {event.event_name}")
        return StopEvent()
