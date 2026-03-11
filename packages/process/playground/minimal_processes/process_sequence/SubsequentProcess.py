from typing import Annotated

from playground.events.CustomProcessStopEvent import CustomProcessStopEvent
from playground.events.InitialProcessWorkEvent import InitialProcessWorkEvent
from swiss_ai_hub.process.agentic_processes.agentic_process import AgenticProcess
from swiss_ai_hub.process.delegators.process.process import Process
from swiss_ai_hub.process.process.decorators.process_step import process_step


class SubsequentProcess(AgenticProcess):
    @process_step()
    async def step(
        self,
        work_from_initial_process: Annotated[
            InitialProcessWorkEvent, Process.In(process_class="InitialProcess", process_id="initial_process")
        ],
    ) -> Annotated[CustomProcessStopEvent, Process.Out()]:
        payload_from_initial = work_from_initial_process.process_stop_event.payload
        print(f"[SubsequentProcess.step] From InitialProcess: {payload_from_initial}")

        final_payload = f"{payload_from_initial} -> SubsequentProcess output"
        return CustomProcessStopEvent(payload=final_payload)
