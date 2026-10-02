from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.events.agent.hitl.response.human_in_the_loop_response_event import HumanInTheLoopResponseEvent
from swiss_ai_hub.core.events.agent.tool_loop.tool_approval_request_event import ToolApprovalRequestEvent


class ToolApprovalResponseEvent(HumanInTheLoopResponseEvent[ToolApprovalRequestEvent]):
    """The user's answer to a tool approval request: run the call, or tell the model it was declined."""

    response: Annotated[bool, Field(description="Whether the user approved the call.")]
