from typing import Annotated

from pydantic import Field

from swiss_ai_hub.api.pagination.page_dto import PageDTO

from .process_walkthrough_dto import ProcessWalkthroughDTO


class PaginatedProcessWalkthroughsResponse(PageDTO):
    """Paginated response containing process walkthroughs with detailed step information."""

    walkthroughs: Annotated[
        list[ProcessWalkthroughDTO],
        Field(description="List of process walkthroughs for the current page"),
    ]
