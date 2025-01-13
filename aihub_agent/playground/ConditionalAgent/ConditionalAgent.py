import random

from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from aihub_lib.nats.events import StartEvent, StopEvent
from playground.ConditionalAgent.Events.EventA import EventA
from playground.ConditionalAgent.Events.EventB import EventB


class ConditionalAgent(Agent):
    @step()
    async def start_step(self, event: StartEvent) -> EventA | EventB:
        if random.random() > 0.5:
            print("[ConditionalAgent.start_step] Sent Event A")
            return EventA()

        print("[ConditionalAgent.start_step] Sent Event B")
        return EventB()

    @step()
    async def end_step(self, event: EventA | EventB) -> StopEvent:
        print(f"[ConditionalAgent.end_step] Received {event.__class__.__name__}")
        return StopEvent()
