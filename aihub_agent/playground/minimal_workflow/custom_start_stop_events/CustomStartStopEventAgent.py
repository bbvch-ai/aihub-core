from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from playground.minimal_workflow.custom_start_stop_events.events.CustomStartEvent import CustomStartEvent
from playground.minimal_workflow.custom_start_stop_events.events.CustomStopEvent import CustomStopEvent


class CustomStartStopEventAgent(Agent):
    @step()
    async def start_step(self, event: CustomStartEvent) -> CustomStopEvent:
        print("[SimpleAgent.start_step]", event)
        return CustomStopEvent(payload=event.payload)
