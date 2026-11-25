from enum import StrEnum


class SearxngTimeRange(StrEnum):
    """How recent SearXNG's results must be, as its `time_range` parameter names it."""

    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"
