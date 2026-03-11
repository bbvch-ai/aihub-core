from typing import Annotated

from swiss_ai_hub.core.form.elements.InputText import InputText
from swiss_ai_hub.core.i18n.LocaleString import LocaleString

from playground.agents.AgentA.events.AgentAStartEvent import AgentAStartEvent
from playground.events.AgentAWorkRequest import AgentAWorkRequest
from playground.events.CustomProcessStopEvent import CustomProcessStopEvent
from playground.events.HumanAWork import HumanAWork
from swiss_ai_hub.process.agentic_processes.AgenticProcess import AgenticProcess
from swiss_ai_hub.process.delegators.agent.Agent import Agent
from swiss_ai_hub.process.delegators.human.Human import Human
from swiss_ai_hub.process.delegators.process.Process import Process
from swiss_ai_hub.process.process.decorators.process_step import process_step


class HumanToAgentProcess(AgenticProcess):
    @process_step()
    async def start_with_human_input_and_delegate_to_agent_a(
        self,
        work_from_human: Annotated[
            HumanAWork,
            Human.In(
                route="/input",
                method="POST",
                start_form=HumanAWork(payload=InputText(label=LocaleString(en="Your input"))),
            ),
        ],
    ) -> Annotated[AgentAWorkRequest, Agent.Out(agent_class="AgentA", agent_id="agent_a")]:
        human_payload = work_from_human.payload
        print(f"[HumanToAgentProcess.start_with_human_input] Received from human: {human_payload}")
        return AgentAWorkRequest(start_event=AgentAStartEvent(payload=human_payload))

    @process_step()
    async def end_with_output_from_agent_a(
        self,
        work_from_agent_a: Annotated[AgentAWorkRequest.work, Agent.In(agent_class="AgentA", agent_id="agent_a")],
    ) -> Annotated[CustomProcessStopEvent, Process.Out()]:
        agent_payload = work_from_agent_a.agent_stop_event.payload
        print(f"[HumanToAgentProcess.end_with_output_from_agent_a] Received from AgentA: {agent_payload}")
        final_payload = f"{agent_payload} -> HumanToAgentProcess output"
        return CustomProcessStopEvent(payload=final_payload)
