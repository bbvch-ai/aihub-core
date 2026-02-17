from typing import Annotated

from aihub_lib.nats.events import ControlEvent
from pydantic import Field


class ToolResultEvent(ControlEvent):
    """Carries a tool result (MCP or agent) back into plan_step."""

    tool_call_id: Annotated[str, Field(description="ID of the tool call this result corresponds to.")]
    tool_name: Annotated[str, Field(description="Name of the tool that produced this result.")]
    result_text: Annotated[str, Field(description="Text result from the tool execution.")]
