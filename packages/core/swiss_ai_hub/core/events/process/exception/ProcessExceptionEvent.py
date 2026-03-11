from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.events.process.work.WorkEvent import WorkEvent


class ProcessExceptionEvent(WorkEvent):
    """
    An event signaling that an exception or error has occurred during a process walkthrough.

    ### Why ProcessExceptionEvent?
    In a complex process, errors might occur either in event transformation or reported by participating entities.
    The `ProcessExceptionEvent` provides a unified way to:
    - Halt or adjust the workflow’s control flow.
    - Communicate the error details to end-users or logging systems.
    """

    message: Annotated[str, Field(description="A human-readable description of the exception or error that occurred.")]
    http_status_code: Annotated[
        int,
        Field(
            description="HTTP status code associated with the exception. Defaults to 500 (Internal Server Error).",
        ),
    ] = 500
