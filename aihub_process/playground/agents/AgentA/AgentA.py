from aihub_agent.workflow.decorators.step import step
from aihub_agent.agents.Agent import Agent

from playground.agents.AgentA.events.AgentAStartEvent import AgentAStartEvent
from playground.agents.AgentA.events.AgentAStopEvent import AgentAStopEvent


class AgentA(Agent):
    @step()
    async def step(self, event: AgentAStartEvent) -> AgentAStopEvent:
        print("[AgentA.step]", event)
        return AgentAStopEvent(payload=event.payload)
