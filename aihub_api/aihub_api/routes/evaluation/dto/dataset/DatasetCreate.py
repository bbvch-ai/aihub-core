from typing import Annotated, List, Optional

from pydantic import BaseModel, Field

from .DatasetItemCreate import DatasetItemCreate


class DatasetCreate(BaseModel):
    dataset_name: Annotated[str, Field(description="The name for the new dataset.", min_length=1)]
    items: Annotated[
        List[DatasetItemCreate], Field(description="A list of question-answer items to include in the dataset.")
    ]
    description: Annotated[Optional[str], Field(description="An optional description for the dataset.")] = None
