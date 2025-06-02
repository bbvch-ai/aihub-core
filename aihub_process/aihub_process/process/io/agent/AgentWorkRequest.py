from pydantic import BaseModel
from aihub_lib.nats.events import StartEvent
from aihub_process.process.io.WorkRequest import WorkRequest


class AgentWorkRequest(WorkRequest):
    agent_class: str
    agent_id: str
    start_event: StartEvent