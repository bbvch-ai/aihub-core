from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.control.stop.StopEvent import StopEvent
from swiss_ai_hub.core.events.agent.ControlAndDisplayEvent import ControlAndDisplayEvent
from swiss_ai_hub.core.i18n.LocaleString import LocaleString


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

    stop_event: Annotated[
        StopEvent,
        Field(
            description="The stop event from the delegated agent containing the task results and marks the completion."
        ),
    ]
