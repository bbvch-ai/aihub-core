from typing import Optional

from aihub_lib.nats.events.process.ProcessEvent import ProcessEvent


class ProcessStopEvent(ProcessEvent):
    process_class: Optional[str] = None
    process_id: Optional[str] = None
    process_walkthrough_id: Optional[str] = None
