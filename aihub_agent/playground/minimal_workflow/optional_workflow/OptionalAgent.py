import random
from typing import List, Optional

from aihub_lib.nats.events import StartEvent, StopEvent

from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from playground.minimal_workflow.optional_workflow.events.EventA import EventA
from playground.minimal_workflow.optional_workflow.events.EventB import EventB
from playground.minimal_workflow.optional_workflow.events.EventC import EventC
from playground.minimal_workflow.optional_workflow.events.EventD import EventD


class OptionalAgent(Agent):
    @step()
    async def start_step(self, event: StartEvent) -> List[EventA | EventB]:
        if random.random() > 0.5:
            print("[OptionalAgent.start_step] Only EventA")
            return [EventA()]
        print("[OptionalAgent.start_step] EventA & EventB")
        return [EventA(), EventB()]

    @step()
    async def optional_step(self, event: EventA, optional_event: Optional[EventB]) -> EventC | EventD:
        if optional_event:
            print("[OptionalAgent.optional_step] Received Optional EventB")
            return EventC()
        print("[OptionalAgent.optional_step] Did not receive Optional EventB")
        return EventD()

    @step(max_executions_per_run=1)
    async def end_step(self, event: EventC | EventD) -> StopEvent:
        print(f"[OptionalAgent.end_step] Received {event.__class__.__name__}")
        return StopEvent()
