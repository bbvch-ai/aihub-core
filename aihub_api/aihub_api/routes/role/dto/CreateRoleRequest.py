from typing import List, Optional, Annotated
from pydantic import BaseModel, Field

class CreateRoleRequest(BaseModel):
    """Request model for creating a new role."""
    name: Annotated[str, Field(description="The unique name of the role.")]
    description: Annotated[str, Field(description="A short description of the role's purpose.")]
    access_rules: Annotated[List[str], Field(default=[], description="A list of access rules granted by this role.")]
