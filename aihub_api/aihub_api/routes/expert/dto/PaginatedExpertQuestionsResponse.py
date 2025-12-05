from typing import Annotated

from pydantic import BaseModel, Field

from aihub_api.routes.expert.dto.ExpertQuestionDTO import ExpertQuestionDTO


class PaginatedExpertQuestionsResponse(BaseModel):
    """A paginated response container for expert questions."""

    total: Annotated[int, Field(description="The total number of questions matching the filter criteria.")]
    page: Annotated[int, Field(description="The current page number (1-indexed).")]
    page_size: Annotated[int, Field(description="The number of questions requested per page.")]
    total_pages: Annotated[int, Field(description="The total number of pages available based on the page size.")]
    questions: Annotated[list[ExpertQuestionDTO], Field(description="The list of questions for the current page.")]
