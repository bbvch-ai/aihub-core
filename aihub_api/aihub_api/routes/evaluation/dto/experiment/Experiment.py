from typing import Optional, Annotated
from pydantic import BaseModel, Field

class Experiment(BaseModel):
    id: Annotated[str, Field(description="The unique identifier of the experiment in Phoenix.")]
    dataset_id: Annotated[str, Field(description="The ID of the dataset associated with this experiment.")]
    dataset_version_id: Annotated[str, Field(description="The version ID of the dataset used.")]
    repetitions: Annotated[int, Field(description="Number of repetitions defined for the experiment.")]
    project_name: Annotated[str, Field(description="The Phoenix project name this experiment belongs to.")]
    name: Annotated[Optional[str], Field(description="The display name of the experiment.")] = None
    description: Annotated[Optional[str], Field(description="The description of the experiment.")] = None
