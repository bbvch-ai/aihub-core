from typing import Annotated

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form.elements.InputText import InputText
from aihub_process.agentic_processes.AgenticProcess import AgenticProcess
from aihub_process.delegators.human.Human import Human
from aihub_process.delegators.process.Process import Process
from aihub_process.process.decorators.process_step import process_step
from playground.events.CustomProcessStopEvent import CustomProcessStopEvent
from playground.events.HumanAWork import HumanAWork
from playground.events.HumanAWorkForm import HumanAWorkForm
from playground.events.HumanBWorkForm import HumanBWorkForm
from playground.events.HumanBWorkReqeust import HumanBWorkRequest


class HumanOnlyProcess(AgenticProcess):
    @process_step()
    async def start_with_output_from_human_a(
        self,
        work_from_human_a: Annotated[
            HumanAWork,
            Human.In(
                route="/input_a",
                method="POST",
                start_form=HumanAWorkForm(payload=InputText(label=LocaleString(en="Input text A"))),
                form=HumanAWorkForm(payload=InputText(label=LocaleString(en="Input text A"))),
            ),
        ],
    ) -> Annotated[HumanBWorkRequest, Human.Out(user_roles=["AIHubAdmin"])]:
        print(f"[AgentOnlyProcess.start_with_output_from_human_a] {work_from_human_a.payload}")
        return HumanBWorkRequest(
            forms=[
                HumanBWorkForm(
                    payload=InputText(
                        label=LocaleString(en=f"Please respond to <{work_from_human_a.payload}> with a single word:")
                    )
                )
            ]
        )

    @process_step()
    async def end_with_output_from_human_b(
        self,
        work_from_human_b: Annotated[
            HumanBWorkRequest.work,
            Human.In(
                route="/input_b",
                method="POST",
                form=HumanBWorkForm(payload=InputText(label=LocaleString(en="Input text A"))),
            ),
        ],
    ) -> Annotated[CustomProcessStopEvent, Process.Out()]:
        print(f"[AgentOnlyProcess.end_with_output_from_human_b] {work_from_human_b.payload}")
        payload = f"{work_from_human_b.payload} -> HumanOnlyProcess output"
        return CustomProcessStopEvent(payload=payload)
