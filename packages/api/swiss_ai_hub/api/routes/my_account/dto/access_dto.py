from typing import Annotated

from pydantic import BaseModel, Field
from swiss_ai_hub.core.auth.access.access_level import AccessLevel


class UserAccess(BaseModel):
    name: Annotated[str, Field(description="Name of the service/agent/process to which access is evaluated")]
    level: Annotated[AccessLevel, Field(description="Access level to the service/agent/process")]


class Access(BaseModel):
    services: Annotated[list[UserAccess], Field(description="List of services and access levels")] = []
    agents: Annotated[list[UserAccess], Field(description="List of agents and access levels")] = []
    processes: Annotated[list[UserAccess], Field(description="List of processes and access levels")] = []
