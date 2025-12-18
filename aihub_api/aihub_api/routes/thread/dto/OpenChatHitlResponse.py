from typing import Annotated, Any

from pydantic import BaseModel, Field


class OpenChatHitlResponse(BaseModel):
    """Response indicating whether there's an open chat HITL request for a thread."""

    has_open_chat_hitl: Annotated[
        bool,
        Field(description="Whether there is an open chat HITL request awaiting response."),
    ]
    hitl_request: Annotated[
        dict[str, Any] | None,
        Field(
            default=None,
            description="The full HITL request event data if there is an open chat HITL, None otherwise.",
        ),
    ]
