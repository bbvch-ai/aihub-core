from typing import Annotated

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form.InputTextElement import InputTextElement

from aihub_process.agentic_processes.AgenticProcess import AgenticProcess
from aihub_process.delegators.human.Human import Human
from aihub_process.delegators.process.Process import Process
from aihub_process.process.decorators.process_step import process_step
from playground.events.CustomProcessStopEvent import CustomProcessStopEvent
from playground.minimal_processes.human_only_process.events.HumanAWork import HumanAWork
from playground.minimal_processes.human_only_process.events.HumanBWork import HumanBWork
from playground.minimal_processes.human_only_process.events.HumanBWorkReqeust import HumanBWorkRequest


class HumanOnlyProcess(AgenticProcess):
    @process_step()
    async def start_with_output_from_human_a(
        self,
        work_from_human_a: Annotated[
            HumanAWork,
            Human.In(
                route="/input_a",
                method="POST",
                start_form=HumanAWork(input_text_a=InputTextElement(label=LocaleString(en="Input text A"))),
            ),
        ],
    ) -> Annotated[HumanBWorkRequest, Human.Out(users=[])]:
        print(f"[AgentOnlyProcess.start_with_output_from_human_a] {work_from_human_a.input_text_a}")
        return HumanBWorkRequest(
            forms=[
                HumanBWork(
                    input_text_b=InputTextElement(
                        label=LocaleString(en=f"Please respond to {work_from_human_a.input_text_a} with a single word:")
                    )
                )
            ]
        )

    @process_step()
    async def end_with_output_from_human_b(
        self, work_from_human_b: Annotated[HumanBWorkRequest.work, Human.In(route="/input_b", method="POST")]
    ) -> Annotated[CustomProcessStopEvent, Process.Out()]:
        print(f"[AgentOnlyProcess.end_with_output_from_human_b] {work_from_human_b.input_text_b}")
        payload = f"{work_from_human_b.input_text_b} -> HumanOnlyProcess output"
        return CustomProcessStopEvent(payload=payload)
