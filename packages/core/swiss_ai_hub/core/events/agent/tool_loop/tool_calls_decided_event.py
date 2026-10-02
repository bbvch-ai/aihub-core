from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.events.agent.control.control_event import ControlEvent
from swiss_ai_hub.core.events.agent.tool_loop.tool_loop_state import ToolLoopState


class ToolCallsDecidedEvent(ControlEvent):
    """The model chose tools in this iteration; the loop continues once every one of them has a result."""

    state: Annotated[ToolLoopState, Field(description="The loop's state including the model's tool-calling turn.")]
    tool_call_ids: Annotated[list[str], Field(description="The calls this iteration waits for.")]
