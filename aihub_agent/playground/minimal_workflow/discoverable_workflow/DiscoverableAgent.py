from aihub_agent.agents.Agent import Agent
from aihub_lib.nats.workflow.decorators.step import step
from aihub_lib.nats.events import StartEvent, StopEvent


class DiscoverableAgent(Agent):
    @step()
    async def start_step(self, event: StartEvent) -> StopEvent:
        print("[DiscoverableAgent.start_step]", event)
        return StopEvent()
