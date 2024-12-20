from pydantic import Field

from aihub_lib.nats.events.control.ControlEvent import ControlEvent
from aihub_lib.nats.events.display.DisplayEvent import DisplayEvent


class ExceptionEvent(ControlEvent, DisplayEvent):
    """
    An event signaling that an exception or error has occurred during a run.

    ### Why ExceptionEvent?
    In a complex, event-driven workflow, errors are inevitable. Some steps might fail due to
    invalid inputs, external service outages, or internal logic errors. The `ExceptionEvent`
    provides a unified way to:
    - Halt or adjust the workflow’s control flow as a `ControlEvent`.
    - Communicate the error details to end-users or logging systems as a `DisplayEvent`.

    By appearing as both a control and display event, `ExceptionEvent` ensures that the workflow
    can stop further processing while also making the error visible in UI dashboards, logs, or
    monitoring tools—giving operators and developers immediate insight into what went wrong.
    """

    message: str = Field(..., description="A human-readable description of the exception or error that occurred.")
