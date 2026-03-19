from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.workflow.decorators.step import step

from playground.agents.agent_a.events.agent_a_start_event import AgentAStartEvent
from playground.agents.agent_a.events.agent_a_stop_event import AgentAStopEvent


class AgentA(Agent):
    @step()
    async def step(self, event: AgentAStartEvent) -> AgentAStopEvent:
        print("[AgentA.step]", event)
        processed_payload = f"{event.payload} -> AgentA processed"
        return AgentAStopEvent(payload=processed_payload)
