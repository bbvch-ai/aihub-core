from typing import Optional, Annotated
from pydantic import BaseModel, Field
from datetime import datetime

class MinimalExperiment(BaseModel):
    id: Annotated[str, Field(description="The unique identifier of the experiment in Phoenix.")]
    name: Annotated[str, Field(description="The name of the experiment.")]
    description: Annotated[Optional[str], Field(description="The description of the experiment.")] = None
    url: Annotated[Optional[str], Field(description="URL to view the experiment in the Phoenix UI.")] = None
    created_at: Annotated[Optional[datetime], Field(description="Timestamp of when the experiment data was recorded or fetched.")] = None
