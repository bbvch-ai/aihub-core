from typing import List, Annotated
from pydantic import Field
from .MinimalDataset import MinimalDataset
from .DatasetItem import DatasetItem

class Dataset(MinimalDataset):
    items: Annotated[List[DatasetItem], Field(description="The list of question-answer items in the dataset.")]