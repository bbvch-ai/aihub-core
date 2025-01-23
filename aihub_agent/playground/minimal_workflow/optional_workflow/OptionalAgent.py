import random
from typing import List, Optional

from aihub_lib.nats.events import StartEvent, StopEvent

from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from playground.minimal_workflow.optional_workflow.events.EventOptionalA import EventOptionalA
from playground.minimal_workflow.optional_workflow.events.EventOptionalB import EventOptionalB
from playground.minimal_workflow.optional_workflow.events.EventOptionalC import EventOptionalC
from playground.minimal_workflow.optional_workflow.events.EventOptionalD import EventOptionalD


class OptionalAgent(Agent):
    @step()
    async def start_step(self, event: StartEvent) -> List[EventOptionalA | EventOptionalB]:
        if random.random() > 0.5:
            print("[OptionalAgent.start_step] Only EventA")
            return [EventOptionalA()]
        print("[OptionalAgent.start_step] EventA & EventB")
        return [EventOptionalA(), EventOptionalB()]

    @step()
    async def optional_step(
        self, event: EventOptionalA, optional_event: Optional[EventOptionalB]
    ) -> EventOptionalC | EventOptionalD:
        if optional_event:
            print("[OptionalAgent.optional_step] Received Optional EventB")
            return EventOptionalC()
        print("[OptionalAgent.optional_step] Did not receive Optional EventB")
        return EventOptionalD()

    @step(max_executions_per_run=1)
    async def end_step(self, event: EventOptionalC | EventOptionalD) -> StopEvent:
        print(f"[OptionalAgent.end_step] Received {event.__class__.__name__}")
        return StopEvent()
