from typing import Annotated

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form.elements.InputText import InputText

from aihub_process.agentic_processes.AgenticProcess import AgenticProcess
from aihub_process.delegators.agent.Agent import Agent
from aihub_process.delegators.human.Human import Human
from aihub_process.delegators.process.Process import Process
from aihub_process.process.decorators.process_step import process_step
from playground.events.AgentAWork import AgentAWork
from playground.events.CustomProcessStopEvent import CustomProcessStopEvent
from playground.events.HumanBWorkForm import HumanBWorkForm
from playground.events.HumanBWorkReqeust import HumanBWorkRequest


class AgentToHumanProcess(AgenticProcess):
    @process_step()
    async def start_with_agent_a_and_request_human_input(
        self,
        work_from_agent_a: Annotated[AgentAWork, Agent.In(agent_class="AgentA", agent_id="agent_a")],
    ) -> Annotated[HumanBWorkRequest, Human.Out(user_roles=["AIHubAdmin"])]:
        agent_payload = work_from_agent_a.agent_stop_event.payload
        print(f"[AgentToHumanProcess.start_with_agent_a] Received from AgentA: {agent_payload}")
        return HumanBWorkRequest(
            forms=[
                HumanBWorkForm(
                    payload=InputText(label=LocaleString(en=f"Please respond to <{agent_payload}> with a single word:"))
                )
            ]
        )

    @process_step()
    async def end_with_human_input(
        self, work_from_human: Annotated[HumanBWorkRequest.work, Human.In(route="/input_b", method="POST")]
    ) -> Annotated[CustomProcessStopEvent, Process.Out()]:
        human_payload = work_from_human.payload
        print(f"[AgentToHumanProcess.end_with_human_input] Received from human: {human_payload}")
        final_payload = f"{human_payload} -> AgentToHumanProcess output"
        return CustomProcessStopEvent(payload=final_payload)
