from pydantic import Field

from aihub_lib.nats.events.control.ControlEvent import ControlEvent
from aihub_lib.nats.events.control.exception.ExceptionEvent import ExceptionEvent
from aihub_lib.nats.events.display.DisplayEvent import DisplayEvent


class AgentInTheLoopExceptionEvent(ControlEvent, DisplayEvent):
    """
    An error response from an agent when a delegated task fails.

    ### Why AgentInTheLoopExceptionEvent?
    When an agent encounters an error during a delegated task, this event:
    - Signals workflow disruption (since it's a `ControlEvent`), allowing error handling in the original agent
    - Is visible to the UI (since it's also a `DisplayEvent`), enabling monitoring and debugging of agent failures
    - Provides a dedicated error channel separate from successful responses
    """

    exception_event: ExceptionEvent = Field(
        ..., description="The exception event from the delegated agent containing error details and failure context."
    )
