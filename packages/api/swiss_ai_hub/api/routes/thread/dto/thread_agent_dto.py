from typing import Annotated

from pydantic import BaseModel, Field
from swiss_ai_hub.core.persistence.messaging.entities.thread_entity import AgentInstanceRef


class ThreadAgentDTO(BaseModel):
    agent_id: Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]+$")]
    agent_class: Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]+$")]

    @classmethod
    def from_agent_ref(cls, agent_ref: AgentInstanceRef):
        return cls(
            agent_id=agent_ref.agent_id,
            agent_class=agent_ref.agent_class,
        )
