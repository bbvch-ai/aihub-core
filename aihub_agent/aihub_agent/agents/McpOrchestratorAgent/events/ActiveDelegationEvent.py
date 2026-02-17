from typing import Annotated, Any

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.nats.events import ControlEvent
from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field


class ActiveDelegationEvent(ControlEvent):
    """Carries the full continuation context for an active agent delegation.

    Consumed by handle_agent_response / handle_agent_exception to reconstruct
    a PlanEvent with the tool result appended to the conversation.
    """

    tool_call_id: Annotated[str, Field(description="Tool call ID of the active agent delegation.")]
    tool_name: Annotated[str, Field(description="Tool name of the active agent delegation.")]
    messages: Annotated[list[ChatMessage], Field(description="Conversation history at the point of delegation.")]
    pending_calls: Annotated[list[dict[str, Any]], Field(default_factory=list, description="Remaining tool calls.")]
    user: Annotated[UserIdentity, Field(description="User identity.")]
