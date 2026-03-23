from typing import Annotated

from playground.events.agent_a_work import AgentAWork
from playground.events.custom_process_stop_event import CustomProcessStopEvent
from swiss_ai_hub.process.agentic_processes.agentic_process import AgenticProcess
from swiss_ai_hub.process.delegators.agent.agent import Agent
from swiss_ai_hub.process.delegators.process.process import Process
from swiss_ai_hub.process.process.decorators.process_step import process_step


class InitialProcess(AgenticProcess):
    @process_step()
    async def step(
        self,
        work_from_agent_a: Annotated[AgentAWork, Agent.In(agent_class="AgentA", agent_id="agent_a")],
    ) -> Annotated[CustomProcessStopEvent, Process.Out()]:
        payload_from_a = work_from_agent_a.agent_stop_event.payload
        print(f"[InitialProcess.step] From AgentA: {payload_from_a}")

        final_payload = f"{payload_from_a} -> InitialProcess output"
        return CustomProcessStopEvent(payload=final_payload)
