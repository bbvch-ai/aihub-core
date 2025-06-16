from aihub_agent.agents.Agent import Agent
from aihub_lib.nats.workflow.decorators.step import step
from playground.minimal_processes.agent_only_process.AgentB.events import AgentBStartEvent
from playground.minimal_processes.agent_only_process.AgentB.events.AgentBStopEvent import AgentBStopEvent


class AgentB(Agent):

    @step()
    async def step(self, event: AgentBStartEvent) -> AgentBStopEvent:
        print("[AgentA.step]", event)
        return AgentBStopEvent(payload=event.payload)