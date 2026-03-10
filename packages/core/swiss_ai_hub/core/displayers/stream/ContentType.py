from enum import StrEnum


class ContentType(StrEnum):
    """Internal enum to represent different types of content being processed."""

    REGULAR = "regular"
    THINKING = "thinking"
