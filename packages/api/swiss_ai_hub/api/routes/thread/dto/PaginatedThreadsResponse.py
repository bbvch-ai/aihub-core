from typing import Annotated

from pydantic import Field

from swiss_ai_hub.api.pagination.PageDTO import PageDTO
from swiss_ai_hub.api.routes.thread.dto.ThreadDTO import ThreadDTO


class PaginatedThreadsResponse(PageDTO):
    threads: Annotated[list[ThreadDTO], Field(description="List of ThreadDTO objects for the current page")]
