from pydantic import Field

from aihub_lib.nats.events.control.stop.StopEvent import StopEvent
from aihub_lib.nats.events.control.ControlEvent import ControlEvent
from aihub_lib.nats.events.display.DisplayEvent import DisplayEvent


class AgentInTheLoopResponseEvent(ControlEvent, DisplayEvent):
    """
    A response from an agent after completing a delegated task.

    ### Why AgentInTheLoopResponseEvent?
    When an agent completes a task delegated through an `AgentInTheLoopRequestEvent`, the response:
    - Influences the workflow (since it's a `ControlEvent`), allowing the original agent to resume based on the result
    - Is visible to the UI (since it's also a `DisplayEvent`), enabling monitoring of agent interactions
    """

    stop_event: StopEvent = Field(
        ...,
        description="The stop event from the delegated agent containing the task results and marks the completion."
    )