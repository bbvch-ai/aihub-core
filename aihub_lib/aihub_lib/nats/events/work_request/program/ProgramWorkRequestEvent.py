from typing import Optional

from aihub_lib.nats.events.work_request.WorkRequestEvent import WorkRequestEvent


class ProgramWorkRequestEvent(WorkRequestEvent):
    """
    WIP
    """

    endpoint: Optional[str] = None
    method: Optional[str] = None
