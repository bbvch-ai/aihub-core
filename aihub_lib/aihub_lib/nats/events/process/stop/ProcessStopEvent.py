from typing import Optional

from aihub_lib.nats.events.work_request.WorkRequestEvent import WorkRequestEvent


class ProcessStopEvent(WorkRequestEvent):
    process_class: Optional[str] = None
    process_id: Optional[str] = None
    process_walkthrough_id: Optional[str] = None
