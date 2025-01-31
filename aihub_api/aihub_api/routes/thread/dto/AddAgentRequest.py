from pydantic import BaseModel


class AddAgentRequest(BaseModel):
    agent_id: str
    agent_class: str
