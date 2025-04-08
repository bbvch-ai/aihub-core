from typing import List

from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.annotations.custom_types.ListOfSize import FixedList
from aihub_agent.workflow.decorators.step import step
from aihub_lib.nats.events import StartEvent, StopEvent
from playground.minimal_workflow.fan_out_workflow.events.FanOutA import FanOutA
from playground.minimal_workflow.fan_out_workflow.events.FanOutB import FanOutB

N = 5


class FanOutAgent(Agent):
    @step()
    async def start_step(self, _: StartEvent) -> List[FanOutA]:
        print("[start_step]")
        return [FanOutA(payload=str(i)) for i in range(N)]

    @step()
    async def process_a(self, event: FanOutA) -> FanOutB:
        return FanOutB(payload=event.payload)

    @step()
    async def stop_step(self, _: FixedList(FanOutB, N)) -> StopEvent:
        print("[stop_step]")
        return StopEvent()
