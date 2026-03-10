from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.api.routes.thread.dto.ThreadAgentDTO import ThreadAgentDTO


class CreateThreadRequest(BaseModel):
    name: str
    user_ids: Annotated[list[str], Field(description="List of user IDs to be associated with the thread")] = []
    agents: Annotated[list[ThreadAgentDTO], Field(description="List of agents to be associated with the thread")] = []
