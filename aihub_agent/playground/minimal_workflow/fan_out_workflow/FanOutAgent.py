from typing import List

from aihub_lib.nats.events import StartEvent, StopEvent

from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.workflow.annotations.custom_types.ListOfSize import FixedList
from aihub_agent.workflow.decorators.step import step
from playground.minimal_workflow.fan_out_workflow.events.FanOutA import FanOutA
from playground.minimal_workflow.fan_out_workflow.events.FanOutB import FanOutB


class FanOutAgent(Agent):
    @step()
    async def start_step(self, event: StartEvent) -> List[FanOutA]:
        print("[FanOutAgent.start_step]", event)
        return [
            FanOutA(payload="1"),
            FanOutA(payload="2"),
            FanOutA(payload="3"),
            FanOutA(payload="4"),
            FanOutA(payload="5"),
        ]

    @step()
    async def process_a(self, event: FanOutA) -> FanOutB:
        print("[FanOutAgent.process_a]", event)
        return FanOutB(payload=event.payload)

    @step()
    async def stop_step(self, events: FixedList(FanOutB, 5)) -> StopEvent:
        print("[FanOutAgent.stop_step]", events)
        return StopEvent()
