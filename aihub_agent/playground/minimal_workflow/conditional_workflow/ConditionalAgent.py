import random

from aihub_lib.nats.events import StartEvent, StopEvent

from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from playground.minimal_workflow.conditional_workflow.events.AboveThresholdEvent import AboveThresholdEvent
from playground.minimal_workflow.conditional_workflow.events.BelowThresholdEvent import BelowThresholdEvent


class ConditionalAgent(Agent):
    @step()
    async def start_step(self, event: StartEvent) -> AboveThresholdEvent | BelowThresholdEvent:
        if random.random() > 0.5:
            print("[ConditionalAgent.start_step] Sent Event A")
            return AboveThresholdEvent()

        print("[ConditionalAgent.start_step] Sent Event B")
        return BelowThresholdEvent()

    @step()
    async def end_step(self, event: AboveThresholdEvent | BelowThresholdEvent) -> StopEvent:
        print(f"[ConditionalAgent.end_step] Received {event.__class__.__name__}")
        return StopEvent()
