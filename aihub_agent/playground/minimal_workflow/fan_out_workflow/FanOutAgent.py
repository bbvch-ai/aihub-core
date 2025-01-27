from typing import List

from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.workflow.annotations.custom_types.ListOfSize import FixedList
from aihub_agent.workflow.decorators.step import step
from aihub_lib.nats.events import StartEvent, StopEvent
from playground.minimal_workflow.fan_out_workflow.events.FanOutEventA import FanOutEventA
from playground.minimal_workflow.fan_out_workflow.events.FanOutEventB import FanOutEventB


class FanOutAgent(Agent):
    @step()
    async def start_step(self, event: StartEvent) -> List[FanOutEventA]:
        print("[FanOutAgent.start_step]", event)
        return [
            FanOutEventA(payload="1"),
            FanOutEventA(payload="2"),
            FanOutEventA(payload="3"),
            FanOutEventA(payload="4"),
            FanOutEventA(payload="5"),
        ]

    @step()
    async def process_a(self, event: FanOutEventA) -> FanOutEventB:
        print("[FanOutAgent.process_a]", event)
        return FanOutEventB(payload=event.payload)

    @step()
    async def stop_step(self, events: FixedList(FanOutEventB, 5)) -> StopEvent:
        print("[FanOutAgent.stop_step]", events)
        return StopEvent()
