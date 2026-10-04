from typing import Annotated, Any

from pydantic import Field

from swiss_ai_hub.core.events.agent.hitl.request.human_in_the_loop_confirmation_request_event import (
    HumanInTheLoopConfirmationRequestEvent,
)


class ToolApprovalRequestEvent(HumanInTheLoopConfirmationRequestEvent):
    """Asks the user to approve a tool call before it runs; chat clients show it as a yes/no confirmation."""

    tool_call_id: Annotated[str, Field(description="The call awaiting approval.")]
    name: Annotated[str, Field(description="The tool the model wants to run.")]
    arguments: Annotated[dict[str, Any], Field(description="The arguments the model passed.")] = {}
    kind: Annotated[str, Field(description="Whether the loop runs it or a capability does.")]
    cite_sources: Annotated[bool, Field(description="Whether the tool tells the model to cite what it returns.")] = True
