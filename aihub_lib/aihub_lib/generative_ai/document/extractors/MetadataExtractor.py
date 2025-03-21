from abc import ABC, abstractmethod
from typing import List

from aihub_lib.generative_ai.document.parsers.Split import Split


class MetadataExtractor(ABC):
    """
    Abstract class for extracting metadata from markdown content.
    """

    @abstractmethod
    def extract(self, splits: List[Split]) -> List[Split]:
        """
        Extract metadata from markdown content.
        """
        return splits
