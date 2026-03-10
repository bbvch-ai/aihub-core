from typing import Annotated

from playground.events.AgentAWork import AgentAWork
from playground.events.CustomProcessStopEvent import CustomProcessStopEvent
from swiss_ai_hub.process.agentic_processes.AgenticProcess import AgenticProcess
from swiss_ai_hub.process.delegators.agent.Agent import Agent
from swiss_ai_hub.process.delegators.process.Process import Process
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
