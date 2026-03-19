from pydantic import BaseModel


class AgentIdentifier(BaseModel):
    """Uniquely identifies an agent."""

    agent_class: str
    agent_id: str

    def __hash__(self):
        return hash((self.agent_class, self.agent_id))

    def __eq__(self, other):
        return (
            isinstance(other, AgentIdentifier)
            and self.agent_class == other.agent_class
            and self.agent_id == other.agent_id
        )
