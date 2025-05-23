from typing import Annotated, List

from aihub_lib.generative_ai.document.types.IngestedDocument import IngestedDocument
from pydantic import Field

from aihub_api.pagination.PageDTO import PageDTO


class PaginatedDocumentsResponse(PageDTO):
    documents: Annotated[
        List[IngestedDocument], Field(description="List of Document DTOs objects for the current page")
    ]
