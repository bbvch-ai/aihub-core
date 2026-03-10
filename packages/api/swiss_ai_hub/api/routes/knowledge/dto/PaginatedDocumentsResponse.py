from typing import Annotated

from pydantic import Field

from swiss_ai_hub.api.pagination.PageDTO import PageDTO
from swiss_ai_hub.api.routes.knowledge.dto.DocumentDTO import DocumentDTO


class PaginatedDocumentsResponse(PageDTO):
    documents: Annotated[
        list[DocumentDTO],
        Field(description="List of Document DTOs objects for the current page"),
    ]
