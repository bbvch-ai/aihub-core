from typing import Annotated

from pydantic import BaseModel, Field


class AddAgentRequest(BaseModel):
    agent_id: Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]+$")]
    agent_class: Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]+$")]
