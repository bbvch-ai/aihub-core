from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent
from swiss_ai_hub.core.events.agent.tool_loop.tool_loop_state import ToolLoopState
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class ToolLoopIterationEvent(ControlAndDisplayEvent):
    """The model's turn to decide: answer, or call tools. One per iteration of the loop."""

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.tool_loop_iteration_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.tool_loop_iteration_event.description"
    )

    state: Annotated[ToolLoopState, Field(description="The loop's state at the start of this iteration.")]
