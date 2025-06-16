from typing import Annotated

from aihub_process.agentic_processes.AgenticProcess import AgenticProcess
from aihub_process.delegators.agent.Agent import Agent
from aihub_process.delegators.process.Process import Process
from aihub_process.process.decorators.process_step import process_step
from playground.minimal_processes.agent_only_process.AgentB.events.AgentBStartEvent import AgentBStartEvent
from playground.minimal_processes.agent_only_process.AgentB.events.CustomProcessStopEvent import CustomProcessStopEvent
from playground.minimal_processes.agent_only_process.events.AgentBWorkRequest import AgentBWorkRequest
from playground.minimal_processes.agent_only_process.events.AgentAWork import AgentAWork


class AgentOnlyProcess(AgenticProcess):
    @process_step()
    async def start_with_output_from_agent_a(
        self,
        work_from_agent_a: Annotated[AgentAWork, Agent.In(agent_class="AgentA", agent_id="agent_a")],
    ) -> Annotated[AgentBWorkRequest, Agent.Out(agent_class="AgentB", agent_id="agent_b")]:
        print(f"[AgentOnlyProcess.start_with_output_from_agent_a] {work_from_agent_a.agent_event.payload}")
        return AgentBWorkRequest(start_event=AgentBStartEvent(payload=work_from_agent_a.agent_event.payload))

    @process_step()
    async def end_with_output_from_agent_b(
        self, work_from_agent_b: Annotated[AgentBWorkRequest.work, Agent.In(agent_class="AgentB", agent_id="agent_b")]
    ) -> Annotated[CustomProcessStopEvent, Process.Out()]:
        print(f"[AgentOnlyProcess.end_with_output_from_agent_b] {work_from_agent_b.agent_event.payload}")
        return CustomProcessStopEvent(payload=work_from_agent_b.agent_event.payload)
