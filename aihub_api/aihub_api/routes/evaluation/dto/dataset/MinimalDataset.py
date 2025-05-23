from datetime import datetime
from typing import Annotated, Optional

from pydantic import BaseModel, Field


class MinimalDataset(BaseModel):
    id: Annotated[str, Field(description="The unique identifier of the dataset in Phoenix.")]
    dataset_name: Annotated[str, Field(description="The name of the dataset.")]
    description: Annotated[Optional[str], Field(description="An optional description for the dataset.")] = None
    created_at: Annotated[Optional[datetime], Field(description="The timestamp when the dataset was created.")] = None
    updated_at: Annotated[Optional[datetime], Field(description="The timestamp when the dataset was last updated.")] = (
        None
    )
