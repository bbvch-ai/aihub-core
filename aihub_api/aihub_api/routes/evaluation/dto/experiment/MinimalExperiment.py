from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from aihub_api.routes.agent.dto.MinimalAgentDTO import MinimalAgentDTO
from aihub_api.routes.evaluation.dto.dataset.MinimalDataset import MinimalDataset


class MinimalExperiment(BaseModel):
    id: Annotated[str, Field(description="The unique identifier of the experiment in Langfuse.")]
    name: Annotated[str, Field(description="The name of the experiment.")]
    description: Annotated[str | None, Field(description="The description of the experiment.")] = None
    agent: Annotated[MinimalAgentDTO, Field(description="Agent that was evaluated")]
    created_at: Annotated[
        datetime | None, Field(description="Timestamp of when the experiment data was recorded or fetched.")
    ] = None
    dataset: Annotated[MinimalDataset, Field(description="The dataset associated with this experiment.")]
    locale: Annotated[str, Field(description="The locale of the experiment.")]
