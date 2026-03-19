from typing import Annotated

from pydantic import BaseModel, Field


class DeleteRoleResponse(BaseModel):
    """Confirmation response for a successful deletion."""

    detail: Annotated[str, Field(description="A confirmation message for the deletion.")] = "Role deleted successfully."
