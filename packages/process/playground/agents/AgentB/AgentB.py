from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.workflow.decorators.step import step

from playground.agents.AgentB.events.AgentBStartEvent import AgentBStartEvent
from playground.agents.AgentB.events.AgentBStopEvent import AgentBStopEvent


class AgentB(Agent):
    @step()
    async def step(self, event: AgentBStartEvent) -> AgentBStopEvent:
        print("[AgentB.step]", event)
        processed_payload = f"{event.payload} -> AgentB processed"
        return AgentBStopEvent(payload=processed_payload)
