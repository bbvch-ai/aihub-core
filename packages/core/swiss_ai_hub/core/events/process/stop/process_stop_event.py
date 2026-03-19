from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.events.process.work.work_event import WorkEvent


class ProcessStopEvent(WorkEvent):
    """
    Signals the successful termination of a process walkthrough.
    """

    process_class: Annotated[
        str | None,
        Field(
            description="Process class associated with this Stop Event. "
            "This field will be auto-ingested by the process dispatcher."
        ),
    ] = None
    process_walkthrough_id: Annotated[
        str | None,
        Field(
            description="Walkthrough ID associated with this Stop Event. "
            "This field will be auto-ingested by the process dispatcher."
        ),
    ] = None
