from typing import Annotated

from pydantic import BaseModel, Field

from .dataset_item_create import DatasetItemCreate


class DatasetUpdate(BaseModel):
    items: Annotated[
        list[DatasetItemCreate],
        Field(description="New question-answer items to append to the dataset."),
    ]
