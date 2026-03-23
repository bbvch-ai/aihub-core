from typing import Annotated

from playground.agents.agent_b.events.agent_b_start_event import AgentBStartEvent
from playground.events.agent_a_work import AgentAWork
from playground.events.agent_b_work_request import AgentBWorkRequest
from playground.events.custom_process_stop_event import CustomProcessStopEvent
from swiss_ai_hub.process.agentic_processes.agentic_process import AgenticProcess
from swiss_ai_hub.process.delegators.agent.agent import Agent
from swiss_ai_hub.process.delegators.process.process import Process
from swiss_ai_hub.process.process.decorators.process_step import process_step


class AgentOnlyProcess(AgenticProcess):
    @process_step()
    async def start_with_output_from_agent_a(
        self,
        work_from_agent_a: Annotated[AgentAWork, Agent.In(agent_class="AgentA", agent_id="agent_a")],
    ) -> Annotated[AgentBWorkRequest, Agent.Out(agent_class="AgentB", agent_id="agent_b")]:
        print(f"[AgentOnlyProcess.start_with_output_from_agent_a] {work_from_agent_a.agent_stop_event.payload}")
        return AgentBWorkRequest(start_event=AgentBStartEvent(payload=work_from_agent_a.agent_stop_event.payload))

    @process_step()
    async def end_with_output_from_agent_b(
        self, work_from_agent_b: Annotated[AgentBWorkRequest.work, Agent.In(agent_class="AgentB", agent_id="agent_b")]
    ) -> Annotated[CustomProcessStopEvent, Process.Out()]:
        print(f"[AgentOnlyProcess.end_with_output_from_agent_b] {work_from_agent_b.agent_stop_event.payload}")
        payload = f"{work_from_agent_b.agent_stop_event.payload} -> AgentOnlyProcess output"
        return CustomProcessStopEvent(payload=payload)
