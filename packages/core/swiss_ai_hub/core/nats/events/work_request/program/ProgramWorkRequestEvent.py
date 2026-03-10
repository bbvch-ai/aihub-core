from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.nats.events.work_request.WorkRequestEvent import WorkRequestEvent


class ProgramWorkRequestEvent(WorkRequestEvent):
    """
    WIP
    """

    endpoint: Annotated[str | None, Field(description="Endpoint to which this work must be submitted")] = None
    method: Annotated[str | None, Field(description="HTTP Method that must be used to submit this piece of work")] = (
        None
    )
