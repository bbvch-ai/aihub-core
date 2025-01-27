from pydantic import BaseModel, Field
from typing import List, Optional


class AuthenticatedUser(BaseModel):
    name: Optional[str] = Field(None, description="User's full name")
    preferred_username: str = Field(..., description="User's email address")
    oid: str = Field(..., description="User's Object ID")
    roles: Optional[List[str]] = Field(..., default_factory=list, description="User's roles")

    def has_access_to_agent(self, agent_class: str, agent_id: str) -> bool:
        return f"{agent_class}.{agent_id}" in self.roles
