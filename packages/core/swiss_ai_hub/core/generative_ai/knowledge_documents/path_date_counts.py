import json
from typing import Annotated, ClassVar, Self

from pydantic import BaseModel, Field

from swiss_ai_hub.core.generative_ai.document.classification.normalized_date import NormalizedDate
from swiss_ai_hub.core.generative_ai.knowledge_documents.path_date_range import PathDateRange
from swiss_ai_hub.core.generative_ai.knowledge_documents.path_date_verdict import PathDateVerdict


class PathDateCounts(BaseModel):
    """How a period sorted the selected documents by the dates in their paths, so the user sees what it left out.

    The examples are bounded in bytes when they are collected, since they ride on every per-document event of a run.
    """

    OUTSIDE_YEAR_LIMIT: ClassVar[int] = 12
    EXCLUDED_EXAMPLE_LIMIT: ClassVar[int] = 10
    EXCLUDED_EXAMPLE_BYTES: ClassVar[int] = 2_000
    EXCLUDED_PATH_CHARACTERS: ClassVar[int] = 200

    in_range: Annotated[int, Field(ge=0, description="Documents whose path dates them in or across the period.")] = 0
    excluded: Annotated[int, Field(ge=0, description="Documents left out, their path dates them outside it.")] = 0
    undated: Annotated[int, Field(ge=0, description="Documents kept, their path gives no clear date.")] = 0
    outside_years: Annotated[
        list[int], Field(description="The years the left-out paths are dated in, the nearest the period first kept.")
    ] = []
    excluded_examples: Annotated[list[str], Field(description="Some of the left-out paths, in listing order.")] = []

    @property
    def total(self) -> int:
        return self.in_range + self.excluded + self.undated

    @classmethod
    def collect(
        cls, outcomes: list[tuple[str, NormalizedDate | None, PathDateVerdict]], date_range: PathDateRange
    ) -> Self:
        counts = dict.fromkeys(PathDateVerdict, 0)
        years: set[int] = set()
        examples: list[str] = []
        example_bytes = 0
        for path, dated, verdict in outcomes:
            counts[verdict] += 1
            if verdict is not PathDateVerdict.OUTSIDE or dated is None:
                continue
            years.update(range(dated.start.year, dated.end.year + 1))
            example = cls._cut(path)
            size = cls._serialized_bytes(example)
            if len(examples) < cls.EXCLUDED_EXAMPLE_LIMIT and example_bytes + size <= cls.EXCLUDED_EXAMPLE_BYTES:
                examples.append(example)
                example_bytes += size
        return cls(
            in_range=counts[PathDateVerdict.WITHIN] + counts[PathDateVerdict.OVERLAPPING],
            excluded=counts[PathDateVerdict.OUTSIDE],
            undated=counts[PathDateVerdict.UNDATED],
            outside_years=cls._nearest(years, date_range),
            excluded_examples=examples,
        )

    @classmethod
    def _nearest(cls, years: set[int], date_range: PathDateRange) -> list[int]:
        nearest = sorted(years, key=lambda year: (date_range.distance_to(year), -year))[: cls.OUTSIDE_YEAR_LIMIT]
        return sorted(nearest)

    @classmethod
    def _cut(cls, path: str) -> str:
        if len(path) <= cls.EXCLUDED_PATH_CHARACTERS:
            return path
        return path[: cls.EXCLUDED_PATH_CHARACTERS - 1] + "…"

    @staticmethod
    def _serialized_bytes(path: str) -> int:
        """The bytes the path adds to an event as `ExtractionTable.serialized_bytes` counts a line: every non-ASCII
        character escaped to six bytes, without the quotes, plus its escaped line break."""
        return len(json.dumps(path)) - 2 + len("\\n")
