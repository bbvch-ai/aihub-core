from typing import Annotated, Any

from pydantic import Field

from aihub_lib.nats.events.work.WorkEvent import WorkEvent


class ProcessStartEvent(WorkEvent):
    """
    An event signaling the start of a new process walkthrough.
    """

    process_config: Annotated["dict[str, Any] | None", Field(description="Process configuration")] = None

    pass
