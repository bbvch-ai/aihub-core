from typing import Annotated

from aihub_api.routes.knowledge.dto.DocumentDTO import DocumentDTO
from pydantic import Field

from aihub_api.pagination.PageDTO import PageDTO


class PaginatedDocumentsResponse(PageDTO):
    documents: Annotated[
        list[DocumentDTO],
        Field(description="List of Document DTOs objects for the current page"),
    ]
