from typing import List, Annotated

from pydantic import BaseModel, Field

from aihub_api.routes.agent.dto.AgentDTO import AgentDTO
from aihub_api.routes.user.dto.UserDTO import UserDTO


class ThreadResponse(BaseModel):
    id: Annotated[str, Field(description="The thread ID")]
    name: Annotated[str, Field(description="User given name of thread")]
    users: Annotated[List[UserDTO], Field(description="List of users in thread")]
    agents: Annotated[List[AgentDTO], Field(description="List of agents in thread")]
    created_at: Annotated[str, Field(description="Date at which thread was created")]