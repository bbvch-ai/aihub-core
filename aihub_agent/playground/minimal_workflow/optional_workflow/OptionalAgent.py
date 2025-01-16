import random
from typing import List, Optional

from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from aihub_lib.nats.events import StartEvent, StopEvent
from playground.minimal_workflow.optional_workflow.events.EventA import EventA
from playground.minimal_workflow.optional_workflow.events.EventB import EventB


class OptionalAgent(Agent):
    @step()
    async def start_step(self, event: StartEvent) -> List[EventA | EventB]:
        if random.random() > 0.5:
            print("[OptionalAgent.start_step] Only EventA")
            return [EventA()]
        print("[OptionalAgent.start_step] EventA & EventB")
        return [EventA(), EventB()]

    @step(max_executions_per_run=1)
    async def end_step(self, event: EventA, optional_event: Optional[EventB]) -> StopEvent:
        if optional_event:
            print("[OptionalAgent.end_step] Received Optional EventB")
        else:
            print("[OptionalAgent.end_step] Did not receive Optional EventB")
        return StopEvent()
