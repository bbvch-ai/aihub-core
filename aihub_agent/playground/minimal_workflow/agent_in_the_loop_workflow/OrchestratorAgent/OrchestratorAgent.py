from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from aihub_lib.nats.events import UserMessageEvent
from aihub_lib.nats.events.agent_in_the_loop.AgentInTheLoop import AgentInTheLoop
from playground.minimal_workflow.agent_in_the_loop_workflow.OrchestratorAgent.Events.OrchestrationResultEvent import (
    OrchestrationResultEvent,
)


class OrchestratorAgent(Agent):
    @step()
    async def start_step(self, event: UserMessageEvent) -> AgentInTheLoop.request:
        print("[OrchestratorAgent.start_step]", event)
        return AgentInTheLoop.invoke(agent_id="worker_agent", agent_class="WorkerAgent", start_event=event)

    @step()
    async def end_step(self, response: AgentInTheLoop.response) -> OrchestrationResultEvent:
        print("[OrchestratorAgent.end_step]", response.stop_event)
        return OrchestrationResultEvent(result=response.stop_event.result)

    @step()
    async def exception_step(self, response: AgentInTheLoop.exception) -> OrchestrationResultEvent:
        print("[OrchestratorAgent.exception_step]", response.exception_event)
        return OrchestrationResultEvent(result=-1)
