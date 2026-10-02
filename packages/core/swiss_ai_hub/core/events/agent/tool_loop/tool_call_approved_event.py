from typing import Annotated, Any, Literal

from pydantic import Field

from swiss_ai_hub.core.events.agent.control.control_event import ControlEvent


class ToolCallApprovedEvent(ControlEvent):
    """A tool call cleared to run, either because it needs no approval or because the user approved it.

    Function tools run in the loop itself; a capability tool's adapter step turns the call into the capability's own
    request, so the call runs the same sub-workflow, with the same events, as an explicit call would.
    """

    tool_call_id: Annotated[str, Field(description="The call's id, which its result answers.")]
    name: Annotated[str, Field(description="The tool to run.")]
    arguments: Annotated[dict[str, Any], Field(description="The arguments the model passed.")] = {}
    kind: Annotated[
        Literal["function", "capability"], Field(description="Whether the loop runs it or a capability does.")
    ]
    cite_sources: Annotated[bool, Field(description="Whether the tool tells the model to cite what it returns.")] = True
