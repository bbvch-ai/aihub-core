from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from playground.agents.AgentB.events.AgentBStartEvent import AgentBStartEvent
from playground.agents.AgentB.events.AgentBStopEvent import AgentBStopEvent


class AgentB(Agent):
    @step()
    async def step(self, event: AgentBStartEvent) -> AgentBStopEvent:
        print("[AgentB.step]", event)
        return AgentBStopEvent(payload=event.payload)
