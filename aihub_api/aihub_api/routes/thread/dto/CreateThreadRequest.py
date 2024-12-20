from typing import List
from pydantic import BaseModel, Field

from aihub_api.routes.thread.dto.ThreadAgentDTO import ThreadAgentDTO


class CreateThreadRequest(BaseModel):
    name: str
    user_ids: List[str] = Field(default_factory=list)
    agents: List[ThreadAgentDTO] = Field(default_factory=list)
