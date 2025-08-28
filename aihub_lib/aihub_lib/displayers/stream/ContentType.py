from enum import Enum


class ContentType(Enum):
    """Internal enum to represent different types of content being processed."""

    REGULAR = "regular"
    THINKING = "thinking"
