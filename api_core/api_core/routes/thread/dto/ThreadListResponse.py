from typing import List
from pydantic import BaseModel

from api_core.routes.thread.dto.ThreadResponse import ThreadResponse


class ThreadListResponse(BaseModel):
    threads: List[ThreadResponse]
