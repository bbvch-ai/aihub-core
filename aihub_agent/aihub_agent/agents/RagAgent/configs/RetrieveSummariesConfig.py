from pydantic import BaseModel


class RetrieveSummariesConfig(BaseModel):
    max_tokens: int
    summary_allocation: float
    content_allocation: float
    parent_allocation: float
    max_parent_levels: int
