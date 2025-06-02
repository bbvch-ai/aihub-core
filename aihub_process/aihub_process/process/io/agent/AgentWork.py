from pydantic import BaseModel

from aihub_lib.nats.events import StopEvent
from aihub_process.process.io.Work import Work


class AgentWork(Work):
    stop_step: StopEvent