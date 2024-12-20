from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from aihub_lib.nats.events import StartEvent, StopEvent


class DiscoverableAgent(Agent):

    @step()
    async def start_step(self, event: StartEvent) -> StopEvent:
        print("[SimpleAgent.start_step]", event)
        return StopEvent()