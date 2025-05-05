from typing import ClassVar

from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.ControlAndDisplayEvent import ControlAndDisplayEvent
from aihub_lib.nats.events.control.stop.StopEvent import StopEvent


class AgentInTheLoopResponseEvent(ControlAndDisplayEvent):
    """
    A response from an agent after completing a delegated task.

    ### Why AgentInTheLoopResponseEvent?
    When an agent completes a task delegated through an `AgentInTheLoopRequestEvent`, the response:
    - Influences the workflow (since it's a `ControlEvent`), allowing the original agent to resume based on the result
    - Is visible to the UI (since it's also a `DisplayEvent`), enabling monitoring of agent interactions
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.aitl_response_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.aitl_response_event.description"
    )

    stop_event: StopEvent = Field(
        ..., description="The stop event from the delegated agent containing the task results and marks the completion."
    )
