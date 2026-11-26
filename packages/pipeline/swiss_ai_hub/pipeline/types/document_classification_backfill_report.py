from collections import Counter
from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.pipeline.types.backfill_work import BackfillWork


class DocumentClassificationBackfillReport(BaseModel):
    """What one classification backfill found to do and did, shown as the run's output metadata.

    Names no document content: failures are listed by document id only.
    """

    dry_run: Annotated[bool, Field(description="Reported the work without doing it")]
    disabled: Annotated[bool, Field(description="The database switched classification off, so nothing was done")] = (
        False
    )
    deleting: Annotated[bool, Field(description="The database is being deleted, so nothing was done")] = False
    planned: Annotated[dict[BackfillWork, int], Field(description="Documents per kind of work owed")] = Field(
        default_factory=dict
    )
    classified: Annotated[int, Field(description="Documents classified with the model")] = 0
    renormalized: Annotated[int, Field(description="Documents whose kept copies were read again, without a model")] = 0
    changed_meanwhile: Annotated[
        int, Field(description="Documents re-ingested or removed while the backfill ran; left to ingestion")
    ] = 0
    failed_document_ids: Annotated[list[str], Field(description="Documents whose backfill failed")] = Field(
        default_factory=list
    )

    def plan(self, works: list[BackfillWork]) -> None:
        self.planned = dict(Counter(works))

    def owed(self, work: BackfillWork) -> int:
        return self.planned.get(work, 0)
