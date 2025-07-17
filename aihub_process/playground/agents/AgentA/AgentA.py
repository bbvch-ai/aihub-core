from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from aihub_lib.agents.AgentConfig import AgentConfig

from playground.agents.AgentA.events.AgentAStartEvent import AgentAStartEvent
from playground.agents.AgentA.events.AgentAStopEvent import AgentAStopEvent


class AgentA(Agent):
    agent_config_type: type[AgentConfig] = AgentConfig

    @step()
    async def step(self, event: AgentAStartEvent) -> AgentAStopEvent:
        print("[AgentA.step]", event)
        processed_payload = f"{event.payload} -> AgentA processed"
        return AgentAStopEvent(payload=processed_payload)
