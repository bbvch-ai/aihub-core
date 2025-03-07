from typing import List

from pydantic import BaseModel

from aihub_api.routes.agent_dynamic.dto.AgentDTO import AgentDTO
from aihub_api.routes.user.dto.UserDTO import UserDTO


class ThreadResponse(BaseModel):
    id: str
    name: str
    users: List[UserDTO]
    agents: List[AgentDTO]
