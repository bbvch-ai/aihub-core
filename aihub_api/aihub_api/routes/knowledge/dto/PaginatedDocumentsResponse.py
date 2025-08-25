from typing import Annotated

from aihub_lib.generative_ai.document.types.IngestedDatalakeFile import IngestedDatalakeFile
from aihub_lib.generative_ai.document.types.IngestedDocument import IngestedDocument
from pydantic import Field

from aihub_api.pagination.PageDTO import PageDTO


class PaginatedDocumentsResponse(PageDTO):
    documents: Annotated[
        list[IngestedDocument | IngestedDatalakeFile], Field(description="List of Document DTOs objects for the current page")
    ]
