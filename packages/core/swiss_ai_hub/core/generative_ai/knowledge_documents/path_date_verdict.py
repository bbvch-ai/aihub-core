from enum import StrEnum


class PathDateVerdict(StrEnum):
    """Where a document's path dates it against a period, which decides whether it is read and judged on the period."""

    WITHIN = "within"
    OVERLAPPING = "overlapping"
    OUTSIDE = "outside"
    UNDATED = "undated"
