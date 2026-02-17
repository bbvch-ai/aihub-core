from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field


class MinimalDataset(BaseModel):
    id: Annotated[str, Field(description="The unique identifier of the dataset in Phoenix.")]
    dataset_name: Annotated[str, Field(description="The name of the dataset.")]
    description: Annotated[str | None, Field(description="An optional description for the dataset.")] = None
    created_at: Annotated[datetime | None, Field(description="The timestamp when the dataset was created.")] = None
    updated_at: Annotated[datetime | None, Field(description="The timestamp when the dataset was last updated.")] = None
