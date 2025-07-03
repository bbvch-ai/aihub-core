from typing import Annotated

from pydantic import BaseModel, Field


class RetrieveSummariesConfig(BaseModel):
    max_parent_levels: Annotated[int, Field(description="Maximum number of parent levels to retrieve summaries from.")] = 2
