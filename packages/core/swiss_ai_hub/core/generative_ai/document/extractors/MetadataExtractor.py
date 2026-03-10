from abc import ABC, abstractmethod

from swiss_ai_hub.core.generative_ai.document.parsers.Split import Split


class MetadataExtractor(ABC):
    """
    Abstract class for extracting metadata from markdown content.
    """

    @abstractmethod
    def extract(self, splits: list[Split]) -> list[Split]:
        """
        Extract metadata from markdown content.
        """
        return splits
