from typing import Annotated, List

from pydantic import BaseModel, Field

from aihub_api.routes.thread.dto.ThreadAgentDTO import ThreadAgentDTO


class CreateThreadRequest(BaseModel):
    name: str
    user_ids: Annotated[List[str], Field()] = []
    agents: Annotated[List[ThreadAgentDTO], Field()] = []
