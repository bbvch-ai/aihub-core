from typing import Annotated, Self

from pydantic import BaseModel, Field

from swiss_ai_hub.core.generative_ai.structured_extraction.extracted_record import ExtractedRecord, RecordValue
from swiss_ai_hub.core.generative_ai.structured_extraction.record_provenance import RecordProvenance


class DocumentExtractionResult(BaseModel):
    """What one document yielded: its records, or the reason it yielded none.

    A failure is a value rather than a raise so that one document a model cannot handle does not cost the records of
    every other document in the same run.
    """

    provenance: Annotated[RecordProvenance, Field(description="Document the extraction ran on")]
    records: Annotated[list[ExtractedRecord], Field(description="Records found, in document order")] = []
    failure_reason: Annotated[
        str | None, Field(description="Why extraction failed; None when it succeeded, even with zero records")
    ] = None
    window_count: Annotated[int, Field(description="Model calls the document was split into")] = 0

    @property
    def failed(self) -> bool:
        return self.failure_reason is not None

    @classmethod
    def succeeded(cls, provenance: RecordProvenance, values: list[dict[str, RecordValue]], window_count: int) -> Self:
        return cls(
            provenance=provenance,
            records=[ExtractedRecord(values=record, provenance=provenance) for record in values],
            window_count=window_count,
        )

    @classmethod
    def failed_with(cls, provenance: RecordProvenance, reason: str, window_count: int) -> Self:
        return cls(provenance=provenance, failure_reason=reason, window_count=window_count)
