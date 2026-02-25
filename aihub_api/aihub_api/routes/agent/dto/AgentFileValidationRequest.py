from typing import Annotated

from pydantic import BaseModel, Field


class AgentFileValidationRequest(BaseModel):
    """Request to validate that a file was uploaded successfully."""

    file_id: Annotated[
        str,
        Field(
            min_length=36,
            max_length=36,
            pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
            description="The file_id (UUID4) returned by the initiate endpoint.",
        ),
    ]
