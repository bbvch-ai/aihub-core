from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from playground.minimal_workflow.custom_start_stop_events.events.MyCustomStartEvent import MyCustomStartEvent
from playground.minimal_workflow.custom_start_stop_events.events.MyCustomStopEvent import MyCustomStopEvent


class CustomStartStopEventAgent(Agent):
    @step()
    async def start_step(self, event: MyCustomStartEvent) -> MyCustomStopEvent:
        print("[SimpleAgent.start_step]", event)
        return MyCustomStopEvent(payload=event.payload)
