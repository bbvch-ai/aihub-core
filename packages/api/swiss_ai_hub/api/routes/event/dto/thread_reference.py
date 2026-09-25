from typing import Annotated

from pydantic import BaseModel, Field


class ThreadReference(BaseModel):
    """The thread that owns a display, resolved so the chat-UI side panel can open the correct per-agent thread."""

    thread_id: Annotated[
        str,
        Field(
            description="The thread ID that owns the requested display, empty when no AI-Hub thread owns it — "
            "which a plain-LLM turn never does."
        ),
    ]
