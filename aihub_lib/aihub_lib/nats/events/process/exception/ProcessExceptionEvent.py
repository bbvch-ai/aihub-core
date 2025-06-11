from pydantic import Field

from aihub_lib.nats.events.process.ProcessEvent import ProcessEvent


class ProcessExceptionEvent(ProcessEvent):
    message: str = Field(..., description="A human-readable description of the exception or error that occurred.")
    http_status_code: int = Field(
        500,
        description="HTTP status code associated with the exception. Defaults to 500 (Internal Server Error).",
    )
