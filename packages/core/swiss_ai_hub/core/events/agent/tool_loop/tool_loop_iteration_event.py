from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.events.agent.control.control_event import ControlEvent
from swiss_ai_hub.core.events.agent.tool_loop.tool_loop_state import ToolLoopState


class ToolLoopIterationEvent(ControlEvent):
    """The model's turn to decide: answer, or call tools. One per iteration of the loop."""

    state: Annotated[ToolLoopState, Field(description="The loop's state at the start of this iteration.")]
