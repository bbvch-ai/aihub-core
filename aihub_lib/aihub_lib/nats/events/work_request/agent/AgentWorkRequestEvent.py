from typing import Generic, Optional, TypeVar

from aihub_lib.nats.events import StartEvent
from aihub_lib.nats.events.work_request.WorkRequestEvent import WorkRequestEvent

TEvent = TypeVar("TEvent", bound=StartEvent)


class AgentWorkRequestEvent(WorkRequestEvent, Generic[TEvent]):
    agent_class: Optional[str] = None
    agent_id: Optional[str] = None
    start_event: TEvent
