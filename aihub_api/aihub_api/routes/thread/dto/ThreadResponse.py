from typing import List

from aihub_lib.persistence.messaging.entities.ThreadEntity import ThreadEntity
from nats.aio.client import Client as NATS
from pydantic import BaseModel

from aihub_api.routes.agent.AgentService import AgentService
from aihub_api.routes.agent.dto.AgentDTO import AgentDTO
from aihub_api.routes.user.dto.UserDTO import UserDTO
from aihub_api.routes.user.UserService import UserService


class ThreadResponse(BaseModel):
    id: str
    name: str
    users: List[UserDTO]
    agents: List[AgentDTO]
