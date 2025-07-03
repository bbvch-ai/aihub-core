from typing import Annotated, Optional

from pydantic import Field

from aihub_lib.nats.events.work_request.WorkRequestEvent import WorkRequestEvent


class ProcessStopEvent(WorkRequestEvent):
    """
    Signals the successful termination of a process walkthrough.
    """

    process_class: Annotated[
        Optional[str],
        Field(
            description="Process class associated with this Stop Event. This field will be auto-ingested by the process dispatcher."
        ),
    ] = None
    process_id: Annotated[
        Optional[str],
        Field(
            description="Process ID associated with this Stop Event. This field will be auto-ingested by the process dispatcher."
        ),
    ] = None
    process_walkthrough_id: Annotated[
        Optional[str],
        Field(
            description="Walkthrough ID associated with this Stop Event. This field will be auto-ingested by the process dispatcher."
        ),
    ] = None
