from aihub_lib.nats.events import StartEvent
from aihub_lib.nats.events.work_request.WorkRequestEvent import WorkRequestEvent


class AgentWorkRequestEvent(WorkRequestEvent):
    agent_class: str
    agent_id: str
    start_event: StartEvent
