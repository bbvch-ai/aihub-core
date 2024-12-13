from typing import List
from pydantic import BaseModel

from api_core.routes.thread.dto.ThreadAgentDTO import ThreadAgentDTO
from api_core.routes.thread.dto.ThreadUserDTO import ThreadUserDTO
from lib_core.persistence.messaging.entities.ThreadEntity import ThreadEntity


class ThreadResponse(BaseModel):
    id: str
    name: str
    users: List[ThreadUserDTO]
    agents: List[ThreadAgentDTO]

    @classmethod
    def from_thread_entity(cls, entity: ThreadEntity):
        return cls(
            id=str(entity.id),
            name=entity.name,
            users=[ThreadUserDTO.from_user_entity(user) for user in entity.users],
            agents=[ThreadAgentDTO.from_agent_entity(agent) for agent in entity.agents]
        )