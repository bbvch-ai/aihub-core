from aihub_lib.nats.events import StartEvent, StopEvent

from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from playground.minimal_workflow.discoverable_workflow.DiscoverableAgentConfig import DiscoverableAgentConfig


class DiscoverableAgent(Agent):
    agent_config_type: type[DiscoverableAgentConfig] = DiscoverableAgentConfig

    @step()
    async def start_step(self, event: StartEvent) -> StopEvent:
        print("[DiscoverableAgent.start_step]", event)
        return StopEvent()
