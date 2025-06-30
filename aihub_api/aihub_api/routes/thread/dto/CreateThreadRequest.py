from typing import Annotated, List

from pydantic import BaseModel, Field

from aihub_api.routes.thread.dto.ThreadAgentDTO import ThreadAgentDTO


class CreateThreadRequest(BaseModel):
    name: str
    user_ids: Annotated[List[str], Field(description="List of user IDs to be associated with the thread")] = []
    agents: Annotated[List[ThreadAgentDTO], Field(description="List of agents to be associated with the thread")] = []
