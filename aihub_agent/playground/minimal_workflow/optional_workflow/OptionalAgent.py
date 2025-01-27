import random
from typing import List, Optional

from aihub_lib.nats.events import StartEvent, StopEvent

from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from playground.minimal_workflow.optional_workflow.events.OptionalEventA import OptionalEventA
from playground.minimal_workflow.optional_workflow.events.OptionalEventB import OptionalEventB
from playground.minimal_workflow.optional_workflow.events.OptionalEventC import OptionalEventC
from playground.minimal_workflow.optional_workflow.events.OptionalEventD import OptionalEventD


class OptionalAgent(Agent):
    @step()
    async def start_step(self, event: StartEvent) -> List[OptionalEventA | OptionalEventB]:
        if random.random() > 0.5:
            print("[OptionalAgent.start_step] Only EventA")
            return [OptionalEventA()]
        print("[OptionalAgent.start_step] EventA & EventB")
        return [OptionalEventA(), OptionalEventB()]

    @step()
    async def optional_step(
            self, event: OptionalEventA, optional_event: Optional[OptionalEventB]
    ) -> OptionalEventC | OptionalEventD:
        if optional_event:
            print("[OptionalAgent.optional_step] Received Optional EventB")
            return OptionalEventC()
        print("[OptionalAgent.optional_step] Did not receive Optional EventB")
        return OptionalEventD()

    @step(max_executions_per_run=1)
    async def end_step(self, event: OptionalEventC | OptionalEventD) -> StopEvent:
        print(f"[OptionalAgent.end_step] Received {event.__class__.__name__}")
        return StopEvent()
