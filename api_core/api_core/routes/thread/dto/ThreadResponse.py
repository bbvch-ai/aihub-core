from typing import List
from pydantic import BaseModel
from nats.aio.client import Client as NATS

from api_core.routes.agent.AgentService import AgentService
from api_core.routes.agent.dto.AgentDTO import AgentDTO
from api_core.routes.user.UserService import UserService
from api_core.routes.user.dto.UserDTO import UserDTO
from lib_core.persistence.messaging.entities.ThreadEntity import ThreadEntity


class ThreadResponse(BaseModel):
    id: str
    name: str
    users: List[UserDTO]
    agents: List[AgentDTO]
