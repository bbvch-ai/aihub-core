from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent
from swiss_ai_hub.core.events.agent.tool_loop.tool_loop_state import ToolLoopState
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class ToolCallsDecidedEvent(ControlAndDisplayEvent):
    """The model chose tools in this iteration; the loop continues once every one of them has a result."""

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.tool_calls_decided_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.tool_calls_decided_event.description"
    )

    state: Annotated[ToolLoopState, Field(description="The loop's state including the model's tool-calling turn.")]
    tool_call_ids: Annotated[list[str], Field(description="The calls this iteration waits for.")]
