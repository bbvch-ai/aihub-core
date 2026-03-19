from typing import Annotated

from pydantic import Field

from swiss_ai_hub.api.pagination.page_dto import PageDTO
from swiss_ai_hub.api.routes.thread.dto.thread_dto import ThreadDTO


class PaginatedThreadsResponse(PageDTO):
    threads: Annotated[list[ThreadDTO], Field(description="List of ThreadDTO objects for the current page")]
