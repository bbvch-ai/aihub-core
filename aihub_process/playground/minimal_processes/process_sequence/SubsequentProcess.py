from typing import Annotated

from aihub_process.agentic_processes.AgenticProcess import AgenticProcess
from aihub_process.delegators.process.Process import Process
from aihub_process.process.decorators.process_step import process_step
from playground.events.CustomProcessStopEvent import CustomProcessStopEvent
from playground.events.InitialProcessWorkEvent import InitialProcessWorkEvent


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
