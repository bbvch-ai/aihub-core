from typing import Annotated

from pydantic import BaseModel, Field


class RetrieveSummariesConfig(BaseModel):
    """Configuration for retrieving parent summary nodes."""

    max_parent_levels: Annotated[
        int, Field(description="Maximum number of parent levels to retrieve summaries from.")
    ] = 2
