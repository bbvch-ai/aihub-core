from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.workflow.decorators.step import step

from playground.agents.AgentC.events.AgentCStartEvent import AgentCStartEvent
from playground.agents.AgentC.events.AgentCStopEvent import AgentCStopEvent


class AgentC(Agent):
    @step()
    async def step(self, event: AgentCStartEvent) -> AgentCStopEvent:
        print("[AgentB.step]", event)
        processed_payload = f"{event.payload} -> AgentC processed"
        return AgentCStopEvent(payload=processed_payload)
