from typing import Annotated, List

from pydantic import Field

from .DatasetItem import DatasetItem
from .MinimalDataset import MinimalDataset


class Dataset(MinimalDataset):
    items: Annotated[List[DatasetItem], Field(description="The list of question-answer items in the dataset.")]
