from swiss_ai_hub.agent.agents.Agent import Agent
from swiss_ai_hub.agent.workflow.decorators.step import step

from playground.agents.AgentA.events.AgentAStartEvent import AgentAStartEvent
from playground.agents.AgentA.events.AgentAStopEvent import AgentAStopEvent


class AgentA(Agent):
    @step()
    async def step(self, event: AgentAStartEvent) -> AgentAStopEvent:
        print("[AgentA.step]", event)
        processed_payload = f"{event.payload} -> AgentA processed"
        return AgentAStopEvent(payload=processed_payload)
