from typing import Annotated

from pydantic import Field

from aihub_api.pagination.PageDTO import PageDTO
from aihub_api.routes.knowledge.dto.DocumentDTO import DocumentDTO


class PaginatedDocumentsResponse(PageDTO):
    documents: Annotated[
        list[DocumentDTO],
        Field(description="List of Document DTOs objects for the current page"),
    ]
