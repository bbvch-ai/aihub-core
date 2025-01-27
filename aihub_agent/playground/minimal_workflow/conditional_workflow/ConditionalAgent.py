import random

from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from aihub_lib.nats.events import StartEvent, StopEvent
from playground.minimal_workflow.conditional_workflow.events.ConditionalEventA import ConditionalEventA
from playground.minimal_workflow.conditional_workflow.events.ConditionalEventB import ConditionalEventB


class ConditionalAgent(Agent):
    @step()
    async def start_step(self, event: StartEvent) -> ConditionalEventA | ConditionalEventB:
        if random.random() > 0.5:
            print("[ConditionalAgent.start_step] Sent Event A")
            return ConditionalEventA()

        print("[ConditionalAgent.start_step] Sent Event B")
        return ConditionalEventB()

    @step()
    async def end_step(self, event: ConditionalEventA | ConditionalEventB) -> StopEvent:
        print(f"[ConditionalAgent.end_step] Received {event.__class__.__name__}")
        return StopEvent()
