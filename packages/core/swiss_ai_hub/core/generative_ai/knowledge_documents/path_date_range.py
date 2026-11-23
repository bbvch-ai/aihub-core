from datetime import date
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, field_serializer, model_validator

from swiss_ai_hub.core.generative_ai.document.classification.date_text_parser import DateTextParser
from swiss_ai_hub.core.generative_ai.document.classification.normalized_date import NormalizedDate
from swiss_ai_hub.core.generative_ai.knowledge_documents.path_date_parser import PathDateParser
from swiss_ai_hub.core.generative_ai.knowledge_documents.path_date_verdict import PathDateVerdict


class PathDateRange(BaseModel):
    """A period the wanted documents are dated in, matched by code against the dates their paths give them.

    Either bound may be open ("since March 2025"), never both. Bounds are inclusive days.
    """

    model_config = ConfigDict(json_schema_mode_override="validation")

    start: Annotated[date | None, Field(description="First day of the period; null when it has no start.")] = None
    end: Annotated[date | None, Field(description="Last day of the period; null when it has no end.")] = None

    @model_validator(mode="after")
    def _one_bound_in_order(self) -> Self:
        if self.start is None and self.end is None:
            raise ValueError("a period needs a start or an end")
        if self.start is not None and self.end is not None and self.start > self.end:
            raise ValueError(f"the period starts on {self.start}, after its end on {self.end}")
        return self

    @field_serializer("start", "end")
    def _iso_day(self, day: date | None) -> str | None:
        """ISO text in every dump mode, since events are stored as BSON, which has no plain date; an instance method
        because `serialize_as_any` skips staticmethod serializers."""
        return None if day is None else day.isoformat()

    @classmethod
    def written(cls, start: str | None, end: str | None) -> Self | None:
        """The period a model wrote as text, or None when it wrote none; a bound that names no date raises. A bound
        written as `YYYY-MM` is read as that month, as a path would be."""
        start, end = (start or "").strip() or None, (end or "").strip() or None
        if start is None and end is None:
            return None
        return cls(start=cls._bound(start, is_start=True), end=cls._bound(end, is_start=False))

    def verdict_of(self, dated: NormalizedDate | None) -> PathDateVerdict:
        if dated is None:
            return PathDateVerdict.UNDATED
        if (self.end is not None and dated.start > self.end) or (self.start is not None and dated.end < self.start):
            return PathDateVerdict.OUTSIDE
        if (self.start is None or dated.start >= self.start) and (self.end is None or dated.end <= self.end):
            return PathDateVerdict.WITHIN
        return PathDateVerdict.OVERLAPPING

    def verdict(self, path: str, today: date | None = None) -> PathDateVerdict:
        return self.verdict_of(PathDateParser.parse(path, today))

    def distance_to(self, year: int) -> int:
        """How many years lie between the year and the period; 0 when they overlap, an open bound never ends."""
        if self.start is not None and year < self.start.year:
            return self.start.year - year
        if self.end is not None and year > self.end.year:
            return year - self.end.year
        return 0

    @staticmethod
    def _bound(value: str | None, is_start: bool) -> date | None:
        if value is None:
            return None
        parsed = DateTextParser.parse(value) or PathDateParser.parse(value)
        if parsed is None:
            raise ValueError(f"'{value}' names no date; write YYYY-MM-DD")
        return parsed.start if is_start else parsed.end
