from typing import Annotated, Tuple

from aihub_process.agentic_processes.AgenticProcess import AgenticProcess
from aihub_process.delegators.agent.Agent import Agent
from aihub_process.delegators.process.Process import Process
from aihub_process.process.decorators.process_step import process_step
from playground.agents.AgentB.events.AgentBStartEvent import AgentBStartEvent
from playground.agents.AgentC.events.AgentCStartEvent import AgentCStartEvent
from playground.events.AgentCWorkRequest import AgentCWorkRequest
from playground.events.AgentBWork import AgentBWork
from playground.events.AgentBWorkRequest import AgentBWorkRequest
from playground.events.AgentAWork import AgentAWork
from playground.events.AgentCWork import AgentCWork
from playground.events.CustomProcessStopEvent import CustomProcessStopEvent


class MultiInputProcess(AgenticProcess):
    @process_step()
    async def start_with_output_from_agent_a(
        self,
        work_from_agent_a: Annotated[AgentAWork, Agent.In(agent_class="AgentA", agent_id="agent_a")],
    ) -> Tuple[
        Annotated[AgentBWorkRequest, Agent.Out(agent_class="AgentB", agent_id="agent_b")],
        Annotated[AgentCWorkRequest, Agent.Out(agent_class="AgentC", agent_id="agent_c")],
    ]:
        print(f"[MultiInputProcess.start_with_output_from_agent_a] {work_from_agent_a.agent_stop_event.payload}")
        return (
            AgentBWorkRequest(start_event=AgentBStartEvent(payload=work_from_agent_a.agent_stop_event.payload)),
            AgentCWorkRequest(start_event=AgentCStartEvent(payload=work_from_agent_a.agent_stop_event.payload)),
        )

    @process_step()
    async def end_with_multiple_events(
        self,
        work_from_agent_b: Annotated[AgentBWork, Agent.In(agent_class="AgentB", agent_id="agent_b")],
        work_from_agent_c: Annotated[AgentCWork, Agent.In(agent_class="AgentC", agent_id="agent_c")],
    ) -> Annotated[CustomProcessStopEvent, Process.Out()]:
        print(
            f"[MultiInputProcess.end_with_multiple_events] work_from_agent_b:{work_from_agent_b.agent_stop_event.payload}"
        )
        print(
            f"[MultiInputProcess.end_with_multiple_events] work_from_agent_c:{work_from_agent_c.agent_stop_event.payload}"
        )
        return CustomProcessStopEvent(
            payload=work_from_agent_b.agent_stop_event.payload + work_from_agent_c.agent_stop_event.payload
        )
