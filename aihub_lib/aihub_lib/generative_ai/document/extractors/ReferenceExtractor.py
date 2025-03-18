from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class Reference:
    """
    Represents a reference extracted from markdown content.
    Implementations can extend this as needed with additional fields.
    """

    ref_id: str
    text: str
    metadata: Optional[Dict] = None


class ReferenceExtractor(ABC):
    """
    Abstract class for extracting references from markdown content.
    """

    @abstractmethod
    def extract_references(self, content: str) -> str:
        """
        Extract references from markdown content.

        Args:
            content (str): The markdown content to extract references from.

        Returns:
            str: The extracted reference.
        """
        pass
