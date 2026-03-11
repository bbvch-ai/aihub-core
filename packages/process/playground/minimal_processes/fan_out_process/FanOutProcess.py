from typing import Annotated

from swiss_ai_hub.core.workflow import FixedList

from playground.agents.AgentB.events.AgentBStartEvent import AgentBStartEvent

# Assuming AgentAWork, AgentBWorkRequest, AgentBStartEvent, CustomProcessStopEvent
# are correctly imported from your playground.events and playground.agents.*.events
from playground.events.AgentAWork import AgentAWork
from playground.events.AgentBWorkRequest import AgentBWorkRequest
from playground.events.CustomProcessStopEvent import CustomProcessStopEvent
from swiss_ai_hub.process.agentic_processes.agentic_process import AgenticProcess
from swiss_ai_hub.process.delegators.agent.agent import Agent
from swiss_ai_hub.process.delegators.process.process import Process
from swiss_ai_hub.process.process.decorators.process_step import process_step


class FanOutProcess(AgenticProcess):
    @process_step()
    async def start_and_fan_out_to_agent_b(
        self,
        work_from_agent_a: Annotated[AgentAWork, Agent.In(agent_class="AgentA", agent_id="agent_a")],
    ) -> tuple[
        Annotated[AgentBWorkRequest, Agent.Out(agent_class="AgentB", agent_id="agent_b")],
        Annotated[AgentBWorkRequest, Agent.Out(agent_class="AgentB", agent_id="agent_b")],
    ]:
        # AgentA's output payload will be the base for AgentB inputs
        base_payload_from_a = work_from_agent_a.agent_stop_event.payload
        print(f"[FanOutProcess.start_and_fan_out_to_agent_b] Received from AgentA: {base_payload_from_a}")

        # Create distinct payloads for the two AgentB instances
        payload_for_b1 = f"{base_payload_from_a} -> Branch 1"
        payload_for_b2 = f"{base_payload_from_a} -> Branch 2"

        return (
            AgentBWorkRequest(start_event=AgentBStartEvent(payload=payload_for_b1)),
            AgentBWorkRequest(start_event=AgentBStartEvent(payload=payload_for_b2)),
        )

    @process_step()
    async def aggregate_and_stop(
        self,
        work_from_agent_b_list: Annotated[
            FixedList(AgentBWorkRequest.work, 2), Agent.In(agent_class="AgentB", agent_id="agent_b")
        ],
    ) -> Annotated[CustomProcessStopEvent, Process.Out()]:
        payload_b1 = work_from_agent_b_list[0].agent_stop_event.payload
        payload_b2 = work_from_agent_b_list[1].agent_stop_event.payload

        print(f"[FanOutProcess.aggregate_and_stop] From AgentB (1): {payload_b1}")
        print(f"[FanOutProcess.aggregate_and_stop] From AgentB (2): {payload_b2}")

        combined_payload = " | ".join(sorted([payload_b1, payload_b2]))
        final_payload = f"{combined_payload} -> FanOutProcess output"
        return CustomProcessStopEvent(payload=final_payload)
