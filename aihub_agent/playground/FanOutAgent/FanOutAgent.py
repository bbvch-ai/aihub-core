from typing import List, Union

from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.workflow.annotations.custom_types.ListOfSize import FixedList
from aihub_agent.workflow.decorators.step import step
from aihub_lib.nats.events import StartEvent, StopEvent
from playground.FanOutAgent.Events.EventA import EventA
from playground.FanOutAgent.Events.EventB import EventB


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
