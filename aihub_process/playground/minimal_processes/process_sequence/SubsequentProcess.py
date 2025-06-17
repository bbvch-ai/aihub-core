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
        work_from_other_process: Annotated[InitialProcessWorkEvent, Process.In(process_class="InitialProcess", process_id="initial_process")],
    ) -> Annotated[CustomProcessStopEvent, Process.Out()]:
        print(f"[SubsequentProcess.step] {work_from_other_process.process_stop_event.payload}")
        return CustomProcessStopEvent(payload=work_from_other_process.process_stop_event.payload)
