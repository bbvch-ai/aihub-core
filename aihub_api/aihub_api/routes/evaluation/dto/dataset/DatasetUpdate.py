from typing import Annotated

from pydantic import BaseModel, Field

from .DatasetItemCreate import DatasetItemCreate


class DatasetUpdate(BaseModel):
    items: Annotated[
        list[DatasetItemCreate],
        Field(
            description="The complete list of new question-answer items. "
            "This will replace all existing items for the dataset version being created/updated."
        ),
    ]
