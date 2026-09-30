from typing import Annotated

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field

from swiss_ai_hub.core.events.agent.control.control_event import ControlEvent
from swiss_ai_hub.core.events.agent.tool_loop.tool_loop_mode import ToolLoopMode


class RunToolLoopEvent(ControlEvent):
    """
    Asks the tool loop to let the model decide which of the blueprint's tools to use, until it is done.

    Built with `ToolLoop.run(...)`; answered with `ToolLoopFinishedEvent`. The tools come from the blueprint's
    declaration, narrowed by the profile and by the features the user switched on for the message.
    """

    history: Annotated[list[ChatMessage], Field(description="The conversation the model decides on.")] = []
    mode: Annotated[ToolLoopMode, Field(description="Whether the loop answers or gathers context.")] = (
        ToolLoopMode.ANSWER
    )
    tools: Annotated[
        list[str] | None, Field(description="Narrows the offered tools to these names for this call, if given.")
    ] = None
    max_iterations: Annotated[
        int | None, Field(description="An iteration limit tighter than the profile's, e.g. 1 for routing.", ge=1)
    ] = None
    cite_sources: Annotated[
        bool, Field(description="Whether tools tell the model to cite what they return, off where it cannot resolve.")
    ] = True
