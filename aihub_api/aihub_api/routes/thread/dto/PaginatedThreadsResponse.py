from typing import List, Annotated

from pydantic import Field

from aihub_api.pagination.PageDTO import PageDTO
from aihub_api.routes.thread.dto.ThreadDTO import ThreadDTO

class PaginatedThreadsResponse(PageDTO):
    threads: Annotated[
        List[ThreadDTO],
        Field(description="List of ThreadDTO objects for the current page")
    ]
