from pydantic import BaseModel
from swiss_ai_hub.core.persistence.messaging.entities.thread_entity import AgentInstanceRef


class ThreadAgentDTO(BaseModel):
    agent_id: str
    agent_class: str

    @classmethod
    def from_agent_ref(cls, agent_ref: AgentInstanceRef):
        return cls(
            agent_id=agent_ref.agent_id,
            agent_class=agent_ref.agent_class,
        )
