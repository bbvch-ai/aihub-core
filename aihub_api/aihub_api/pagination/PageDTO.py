from typing import Annotated

from pydantic import BaseModel, Field


class PageDTO(BaseModel):
    total: Annotated[int, Field(description="Total number of items available")]
    page: Annotated[int, Field(description="Current page number (1-indexed)")]
    page_size: Annotated[int, Field(description="Number of threads per page")]
    total_pages: Annotated[int, Field(description="Total number of pages available")]
