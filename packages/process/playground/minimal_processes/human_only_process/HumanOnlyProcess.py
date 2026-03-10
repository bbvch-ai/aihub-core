from typing import Annotated

from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.nats.events.form.elements.InputText import InputText

from playground.events.CustomProcessStopEvent import CustomProcessStopEvent
from playground.events.HumanAWork import HumanAWork
from playground.events.HumanBWork import HumanBWork
from playground.events.HumanBWorkReqeust import HumanBWorkRequest
from swiss_ai_hub.process.agentic_processes.AgenticProcess import AgenticProcess
from swiss_ai_hub.process.delegators.human.Human import Human
from swiss_ai_hub.process.delegators.process.Process import Process
from swiss_ai_hub.process.process.decorators.process_step import process_step


class HumanOnlyProcess(AgenticProcess):
    @process_step()
    async def start_with_output_from_human_a(
        self,
        work_from_human_a: Annotated[
            HumanAWork,
            Human.In(
                route="/input_a",
                method="POST",
                start_form=HumanAWork(payload=InputText(label=LocaleString(en="Input text A"))),
            ),
        ],
    ) -> Annotated[HumanBWorkRequest, Human.Out(user_roles=["AIHubAdmin"])]:
        print(f"[AgentOnlyProcess.start_with_output_from_human_a] {work_from_human_a.payload}")
        return HumanBWorkRequest(
            forms=[
                HumanBWork(
                    payload=InputText(
                        label=LocaleString(en=f"Please respond to <{work_from_human_a.payload}> with a single word:")
                    )
                )
            ]
        )

    @process_step()
    async def end_with_output_from_human_b(
        self, work_from_human_b: Annotated[HumanBWorkRequest.work, Human.In(route="/input_b", method="POST")]
    ) -> Annotated[CustomProcessStopEvent, Process.Out()]:
        print(f"[AgentOnlyProcess.end_with_output_from_human_b] {work_from_human_b.payload}")
        payload = f"{work_from_human_b.payload} -> HumanOnlyProcess output"
        return CustomProcessStopEvent(payload=payload)
