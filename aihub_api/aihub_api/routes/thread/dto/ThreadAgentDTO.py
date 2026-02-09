from aihub_lib.persistence.messaging.entities.ThreadEntity import AgentInstanceRef
from pydantic import BaseModel


class ThreadAgentDTO(BaseModel):
    agent_id: str
    agent_class: str

    @classmethod
    def from_agent_ref(cls, agent_ref: AgentInstanceRef):
        return cls(
            agent_id=agent_ref.agent_id,
            agent_class=agent_ref.agent_class,
        )
