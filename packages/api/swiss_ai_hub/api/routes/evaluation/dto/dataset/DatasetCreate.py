from typing import Annotated

from pydantic import BaseModel, Field

from .DatasetItemCreate import DatasetItemCreate


class DatasetCreate(BaseModel):
    dataset_name: Annotated[str, Field(description="The name for the new dataset.", min_length=1)]
    items: Annotated[
        list[DatasetItemCreate], Field(description="A list of question-answer items to include in the dataset.")
    ]
    description: Annotated[str | None, Field(description="An optional description for the dataset.")] = None
