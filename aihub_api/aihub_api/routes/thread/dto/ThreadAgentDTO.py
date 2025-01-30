from pydantic import BaseModel

from aihub_lib.persistence.messaging.entities.ThreadEntity import Agent


class ThreadAgentDTO(BaseModel):
    agent_id: str
    agent_class: str

    @classmethod
    def from_agent_entity(cls, agent: Agent):
        return cls(
            agent_id=agent.agent_id,
            agent_class=agent.agent_id,
        )
