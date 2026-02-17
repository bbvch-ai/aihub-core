from typing import Annotated, Any

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.nats.events import ControlEvent
from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field


class PlanEvent(ControlEvent):
    """Triggers the plan step with the current conversation state."""

    messages: Annotated[list[ChatMessage], Field(description="Conversation history.")]
    pending_calls: Annotated[list[dict[str, Any]], Field(default_factory=list, description="Remaining tool calls.")]
    user: Annotated[UserIdentity, Field(description="User identity.")]
