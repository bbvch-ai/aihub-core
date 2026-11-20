from typing import Annotated, Self

from pydantic import BaseModel, Field

from swiss_ai_hub.core.generative_ai.structured_extraction.document_match import DocumentMatch
from swiss_ai_hub.core.generative_ai.structured_extraction.extracted_record import ExtractedRecord, RecordValue
from swiss_ai_hub.core.generative_ai.structured_extraction.record_provenance import RecordProvenance


class DocumentExtractionResult(BaseModel):
    """What one document yielded: its records, or the reason it yielded none.

    A failure is a value rather than a raise so that one document a model cannot handle does not cost the records of
    every other document in the same run. A document that clearly fails the document condition is skipped, which is a
    result too and never a failure.
    """

    provenance: Annotated[RecordProvenance, Field(description="Document the extraction ran on")]
    records: Annotated[list[ExtractedRecord], Field(description="Records found, in document order")] = []
    failure_reason: Annotated[
        str | None, Field(description="Why extraction failed; None when it succeeded, even with zero records")
    ] = None
    window_count: Annotated[int, Field(description="Windows the document was split into")] = 0
    partial: Annotated[
        bool,
        Field(description="Whether only some windows were read, so records outside them may be missing"),
    ] = False
    document_match: Annotated[
        DocumentMatch | None,
        Field(description="How the document met the document condition; None without one"),
    ] = None

    @property
    def failed(self) -> bool:
        return self.failure_reason is not None

    @property
    def skipped(self) -> bool:
        return self.document_match is not None and self.document_match.fails

    @classmethod
    def succeeded(
        cls,
        provenance: RecordProvenance,
        values: list[dict[str, RecordValue]],
        window_count: int,
        partial: bool = False,
        document_match: DocumentMatch | None = None,
    ) -> Self:
        return cls(
            provenance=provenance,
            records=[ExtractedRecord(values=record, provenance=provenance) for record in values],
            window_count=window_count,
            partial=partial,
            document_match=document_match,
        )

    @classmethod
    def skipped_by(cls, provenance: RecordProvenance, document_match: DocumentMatch, window_count: int) -> Self:
        """No records, even those the model listed with its "no", since the whole document does not count."""
        return cls(provenance=provenance, window_count=window_count, document_match=document_match)

    @classmethod
    def failed_with(cls, provenance: RecordProvenance, reason: str, window_count: int) -> Self:
        return cls(provenance=provenance, failure_reason=reason, window_count=window_count)
