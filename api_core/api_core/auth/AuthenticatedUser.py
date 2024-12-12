from pydantic import BaseModel, Field
from typing import List, Optional


class AuthenticatedUser(BaseModel):
    name: Optional[str] = Field(None, description="User's full name")
    preferred_username: str = Field(..., description="User's email address")
    oid: str = Field(..., description="User's Object ID")
    roles: Optional[List[str]] = Field(..., default_factory=list, description="User's roles")