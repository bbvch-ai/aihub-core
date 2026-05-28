from typing import Annotated

from pydantic import BaseModel, Field


class AssignRoleRequest(BaseModel):
    role_name: Annotated[str, Field(description="Name of the tenant role to assign to the user.", min_length=1)]
