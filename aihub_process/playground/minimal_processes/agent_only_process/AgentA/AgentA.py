from aihub_lib.nats.workflow.decorators.step import step
from aihub_agent.agents.Agent import Agent

from playground.minimal_processes.agent_only_process.AgentA.events.AgentAStartEvent import AgentAStartEvent
from playground.minimal_processes.agent_only_process.AgentA.events.AgentAStopEvent import AgentAStopEvent


class AgentA(Agent):

    @step()
    async def step(self, event: AgentAStartEvent) -> AgentAStopEvent:
        print("[AgentA.step]", event)
        return AgentAStopEvent(payload=event.payload)