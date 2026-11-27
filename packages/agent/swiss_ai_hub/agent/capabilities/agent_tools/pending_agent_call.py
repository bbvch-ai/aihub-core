from typing import Annotated

from pydantic import BaseModel, Field


class PendingAgentCall(BaseModel):
    """A delegation the model's tool call started, and the call its answer belongs to."""

    tool_call_id: Annotated[str, Field(description="The tool call the answer goes back to.")]
    tool_name: Annotated[str, Field(description="The tool the model called.")]
