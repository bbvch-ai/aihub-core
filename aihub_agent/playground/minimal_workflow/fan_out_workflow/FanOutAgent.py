from typing import List

from aihub_lib.testing.logging.logger import enable_logging

from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.workflow.annotations.custom_types.ListOfSize import FixedList
from aihub_agent.workflow.decorators.step import step
from aihub_lib.nats.events import StartEvent, StopEvent
from playground.minimal_workflow.fan_out_workflow.events.EventA import EventA
from playground.minimal_workflow.fan_out_workflow.events.EventB import EventB


enable_logging()


class FanOutAgent(Agent):

    @step()
    async def start_step(self, event: StartEvent) -> List[EventA]:
        print(f"[FanOutAgent.start_step]", event)
        return [
            EventA(payload="1"),
            EventA(payload="2"),
            EventA(payload="3"),
            EventA(payload="4"),
            EventA(payload="5"),
        ]

    @step()
    async def process_a(self, event: EventA) -> EventB:
        print(f"[FanOutAgent.process_a]", event)
        return EventB(payload=event.payload)

    @step()
    async def stop_step(self, events: FixedList(EventB, 5)) -> StopEvent:
        print(f"[FanOutAgent.stop_step]", events)
        return StopEvent()
