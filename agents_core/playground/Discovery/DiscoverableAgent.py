from agents_core.agents.abstract.Agent import Agent
from agents_core.workflow.decorators.step import step
from lib_core.nats.events import StartEvent, StopEvent


class DiscoverableAgent(Agent):

    @step()
    async def start_step(self, event: StartEvent) -> StopEvent:
        print("[SimpleAgent.start_step]", event)
        return StopEvent()