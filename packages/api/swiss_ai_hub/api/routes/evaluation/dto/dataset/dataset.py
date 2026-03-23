from typing import Annotated

from pydantic import Field

from .dataset_item import DatasetItem
from .minimal_dataset import MinimalDataset


class Dataset(MinimalDataset):
    items: Annotated[list[DatasetItem], Field(description="The list of question-answer items in the dataset.")]
