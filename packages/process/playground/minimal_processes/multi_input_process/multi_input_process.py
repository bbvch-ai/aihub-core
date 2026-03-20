from typing import Annotated

from playground.agents.agent_b.events.agent_b_start_event import AgentBStartEvent
from playground.agents.agent_c.events.agent_c_start_event import AgentCStartEvent
from playground.events.agent_a_work import AgentAWork
from playground.events.agent_b_work_request import AgentBWorkRequest
from playground.events.agent_c_work_request import AgentCWorkRequest
from playground.events.custom_process_stop_event import CustomProcessStopEvent
from swiss_ai_hub.process.agentic_processes.agentic_process import AgenticProcess
from swiss_ai_hub.process.delegators.agent.agent import Agent
from swiss_ai_hub.process.delegators.process.process import Process
from swiss_ai_hub.process.process.decorators.process_step import process_step


class MultiInputProcess(AgenticProcess):
    @process_step()
    async def start_and_delegate_to_b_and_c(
        self,
        work_from_agent_a: Annotated[AgentAWork, Agent.In(agent_class="AgentA", agent_id="agent_a")],
    ) -> tuple[
        Annotated[AgentBWorkRequest, Agent.Out(agent_class="AgentB", agent_id="agent_b")],
        Annotated[AgentCWorkRequest, Agent.Out(agent_class="AgentC", agent_id="agent_c")],
    ]:
        payload_from_a = work_from_agent_a.agent_stop_event.payload
        print(f"[MultiInputProcess.start_and_delegate_to_b_and_c] From AgentA: {payload_from_a}")

        return (
            AgentBWorkRequest(start_event=AgentBStartEvent(payload=payload_from_a)),
            AgentCWorkRequest(start_event=AgentCStartEvent(payload=payload_from_a)),
        )

    @process_step()
    async def aggregate_from_b_and_c_and_stop(
        self,
        work_from_agent_b: Annotated[AgentBWorkRequest.work, Agent.In(agent_class="AgentB", agent_id="agent_b")],
        work_from_agent_c: Annotated[AgentCWorkRequest.work, Agent.In(agent_class="AgentC", agent_id="agent_c")],
    ) -> Annotated[CustomProcessStopEvent, Process.Out()]:
        payload_from_b = work_from_agent_b.agent_stop_event.payload
        payload_from_c = work_from_agent_c.agent_stop_event.payload

        print(f"[MultiInputProcess.aggregate_from_b_and_c_and_stop] From AgentB: {payload_from_b}")
        print(f"[MultiInputProcess.aggregate_from_b_and_c_and_stop] From AgentC: {payload_from_c}")

        combined_payload_from_agents = " | ".join(sorted([payload_from_b, payload_from_c]))

        final_payload = f"{combined_payload_from_agents} -> MultiInputProcess output"
        return CustomProcessStopEvent(payload=final_payload)
