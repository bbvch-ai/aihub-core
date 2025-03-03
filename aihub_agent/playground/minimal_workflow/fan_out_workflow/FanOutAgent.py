from time import time
from typing import List

from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.workflow.annotations.custom_types.ListOfSize import FixedList
from aihub_agent.workflow.decorators.step import step
from aihub_lib.nats.events import StartEvent, StopEvent
from playground.minimal_workflow.fan_out_workflow.events.FanOutA import FanOutA
from playground.minimal_workflow.fan_out_workflow.events.FanOutB import FanOutB

N = 5

start = time()


class FanOutAgent(Agent):
    @step()
    async def start_step(self, event: StartEvent) -> List[FanOutA]:
        global start
        start = time()
        print("[FanOutAgent.start_step]", event)
        return [FanOutA(payload=str(i)) for i in range(N)]

    @step()
    async def process_a(self, event: FanOutA) -> FanOutB:
        print("[FanOutAgent.process_a]", event)
        return FanOutB(payload=event.payload)

    @step()
    async def stop_step(self, events: FixedList(FanOutB, N)) -> StopEvent:
        print("[FanOutAgent.stop_step]", events)
        print("Time taken:", time() - start)
        return StopEvent()
