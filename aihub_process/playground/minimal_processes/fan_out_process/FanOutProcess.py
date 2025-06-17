from typing import Annotated, Tuple

from aihub_lib.nats.workflow.annotations.custom_types.ListOfSize import FixedList
from aihub_process.agentic_processes.AgenticProcess import AgenticProcess
from aihub_process.delegators.agent.Agent import Agent
from aihub_process.delegators.process.Process import Process
from aihub_process.process.decorators.process_step import process_step
from playground.agents.AgentB.events.AgentBStartEvent import AgentBStartEvent
from playground.events.AgentBWorkRequest import AgentBWorkRequest
from playground.events.AgentAWork import AgentAWork
from playground.events.CustomProcessStopEvent import CustomProcessStopEvent


class FanOutProcess(AgenticProcess):
    @process_step()
    async def start_with_output_from_agent_a(
        self,
        work_from_agent_a: Annotated[AgentAWork, Agent.In(agent_class="AgentA", agent_id="agent_a")],
    ) -> Tuple[
        Annotated[AgentBWorkRequest, Agent.Out(agent_class="AgentB", agent_id="agent_b")],
        Annotated[AgentBWorkRequest, Agent.Out(agent_class="AgentB", agent_id="agent_b")],
    ]:
        print(f"[FanOutProcess.start_with_output_from_agent_a] {work_from_agent_a.agent_stop_event.payload}")
        return (
            AgentBWorkRequest(start_event=AgentBStartEvent(payload="1")),
            AgentBWorkRequest(start_event=AgentBStartEvent(payload="2")),
        )

    @process_step()
    async def end_with_output_from_agent_b(
        self,
        work_from_agent_b: Annotated[
            FixedList(AgentBWorkRequest.work, 2), Agent.In(agent_class="AgentB", agent_id="agent_b")
        ],
    ) -> Annotated[CustomProcessStopEvent, Process.Out()]:
        print(f"[FanOutProcess.end_with_output_from_agent_b.0] {work_from_agent_b[0].agent_stop_event.payload}")
        print(f"[FanOutProcess.end_with_output_from_agent_b.1] {work_from_agent_b[1].agent_stop_event.payload}")
        return CustomProcessStopEvent(payload="done")
