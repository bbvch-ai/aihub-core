from typing import Annotated

from pydantic import BaseModel, Field
from swiss_ai_hub.core.events.agent import HumanInTheLoopRequestEvent


class OpenChatHitlResponse(BaseModel):
    """Response indicating whether there's an open chat HITL request for a thread."""

    has_open_chat_hitl: Annotated[
        bool,
        Field(description="Whether there is an open chat HITL request awaiting response."),
    ]
    hitl_request: Annotated[
        HumanInTheLoopRequestEvent | None,
        Field(
            default=None,
            description="The HITL request event if there is an open chat HITL, None otherwise.",
        ),
    ]
