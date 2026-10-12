from typing import Annotated

from pydantic import BaseModel, Field


class AgentFileBatchValidationResponse(BaseModel):
    """Which of the checked files the agent's bucket does not hold; uploads expire, so a known file can be gone."""

    missing: Annotated[list[str], Field(description="The file_ids not found in the agent's bucket.")]
