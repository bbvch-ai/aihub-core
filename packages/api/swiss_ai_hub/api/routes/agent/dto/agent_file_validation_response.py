from typing import Annotated

from pydantic import BaseModel, Field


class AgentFileValidationResponse(BaseModel):
    """Response confirming whether a file exists in the agent's bucket."""

    file_id: Annotated[str, Field(description="The file_id that was checked.")]
    exists: Annotated[bool, Field(description="True if the file was found in the agent's bucket.")]
