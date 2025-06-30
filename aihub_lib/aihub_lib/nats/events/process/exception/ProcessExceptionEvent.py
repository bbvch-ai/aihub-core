from pydantic import Field

from aihub_lib.nats.events.process.ProcessEvent import ProcessEvent


class ProcessExceptionEvent(ProcessEvent):
    """
    An event signaling that an exception or error has occurred during a process walkthrough.

    ### Why ProcessExceptionEvent?
    In a complex process, errors might occur either in event transformation or reported by participating entities.
    The `ProcessExceptionEvent` provides a unified way to:
    - Halt or adjust the workflow’s control flow.
    - Communicate the error details to end-users or logging systems.
    """

    message: str = Field(..., description="A human-readable description of the exception or error that occurred.")
    http_status_code: int = Field(
        500,
        description="HTTP status code associated with the exception. Defaults to 500 (Internal Server Error).",
    )
