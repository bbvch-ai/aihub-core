from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from aihub_lib.agents.AgentConfig import AgentConfig

from playground.agents.AgentB.events.AgentBStartEvent import AgentBStartEvent
from playground.agents.AgentB.events.AgentBStopEvent import AgentBStopEvent


class AgentB(Agent):
    agent_config_type: type[AgentConfig] = AgentConfig

    @step()
    async def step(self, event: AgentBStartEvent) -> AgentBStopEvent:
        print("[AgentB.step]", event)
        processed_payload = f"{event.payload} -> AgentB processed"
        return AgentBStopEvent(payload=processed_payload)
