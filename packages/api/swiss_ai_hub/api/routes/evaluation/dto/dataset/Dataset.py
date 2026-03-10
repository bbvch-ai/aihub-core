from typing import Annotated

from pydantic import Field

from .DatasetItem import DatasetItem
from .MinimalDataset import MinimalDataset


class Dataset(MinimalDataset):
    items: Annotated[list[DatasetItem], Field(description="The list of question-answer items in the dataset.")]
