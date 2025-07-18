from typing import Annotated

from pydantic import Field

from aihub_api.pagination.PageDTO import PageDTO
from aihub_api.routes.thread.dto.ThreadDTO import ThreadDTO


class PaginatedThreadsResponse(PageDTO):
    threads: Annotated[list[ThreadDTO], Field(description="List of ThreadDTO objects for the current page")]
