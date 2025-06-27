from pydantic import BaseModel


class RetrieveSummariesConfig(BaseModel):
    max_parent_levels: int
