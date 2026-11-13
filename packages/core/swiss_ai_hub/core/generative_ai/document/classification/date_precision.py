from enum import StrEnum


class DatePrecision(StrEnum):
    """How much of a date the document states, so "März 2025" is never read back as 1 March."""

    DAY = "day"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"
