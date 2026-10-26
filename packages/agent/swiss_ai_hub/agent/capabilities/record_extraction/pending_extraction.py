from typing import Annotated, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.generative_ai import BucketNamespacePair, KnowledgeDocumentSummary, RecordSchema

from swiss_ai_hub.agent.context.thread.thread_context import ThreadContext

PENDING_KEY = "record_extraction:pending"


class PendingExtraction(BaseModel):
    """An extraction a conversation has not finished: the documents and rows the user can still ask for.

    More documents matched than one answer extracts, or one answer found more rows than it shows. Nothing is dropped:
    the rest waits here, per conversation, until the user continues or asks something new, which replaces it. A part
    is taken before it runs, so a repeated continue goes on with the next one, and finished once its table is
    assembled, so a part whose run died is extracted again rather than counted. It lives
    in the thread context rather than on events because a thousand documents would not fit a message, and it keeps the
    columns so every part of one extraction has the same table.
    """

    extraction_id: Annotated[str, Field(description="The extraction the parts belong to.")]
    documents: Annotated[list[KnowledgeDocumentSummary], Field(description="Every selected document, in order.")] = []
    part_starts: Annotated[
        list[int], Field(description="Index of each part's first document; the last part ends with the list.")
    ] = []
    next_part: Annotated[int, Field(description="The first part no continue has taken yet, from 0.")] = 0
    finished_parts: Annotated[
        list[int], Field(description="Parts whose table was assembled; a taken part missing here never finished.")
    ] = []
    record_schema: Annotated[RecordSchema | None, Field(description="The columns every part extracts.")] = None
    instructions: Annotated[str | None, Field(description="Which records to keep.")] = None
    row_terms: Annotated[str | None, Field(description="What lines holding wanted records usually contain.")] = None
    criteria: Annotated[str, Field(description="How the documents were selected, for the summary.")] = ""
    collections: Annotated[list[BucketNamespacePair], Field(description="The collections selected from.")] = []
    show_collection: Annotated[bool, Field(description="Whether rows name their collection.")] = False
    columns: Annotated[list[str], Field(description="The rendered table's header, once a part was shown.")] = []
    overflow_rows: Annotated[list[str], Field(description="Rendered table rows not shown yet.")] = []
    extracted_files: Annotated[int, Field(description="Documents extracted so far.")] = 0
    rows_found: Annotated[int, Field(description="Rows found so far.")] = 0
    failed_files: Annotated[int, Field(description="Documents that failed so far.")] = 0

    @property
    def part_count(self) -> int:
        return len(self.part_starts)

    @property
    def remaining_documents(self) -> int:
        return sum(len(self.part(index)) for index in range(self.part_count) if index not in self.finished_parts)

    @property
    def following_part(self) -> int | None:
        """The part a continue extracts: the next one not taken, then any taken part whose run never finished."""
        if self.next_part < self.part_count:
            return self.next_part
        return next((index for index in range(self.part_count) if index not in self.finished_parts), None)

    def taking(self, index: int) -> Self:
        return self.model_copy(update={"next_part": max(self.next_part, index + 1)})

    def finishing(self, index: int) -> Self:
        return self.model_copy(update={"finished_parts": sorted({*self.finished_parts, index})})

    def part(self, index: int) -> list[KnowledgeDocumentSummary]:
        end = self.part_starts[index + 1] if index + 1 < self.part_count else len(self.documents)
        return self.documents[self.part_starts[index] : end]

    @classmethod
    async def load(cls, thread: ThreadContext) -> Self | None:
        stored = await thread.get(PENDING_KEY)
        return cls.model_validate(stored) if stored else None

    async def save(self, thread: ThreadContext) -> None:
        await thread.set(PENDING_KEY, self.model_dump(mode="json"))

    @staticmethod
    async def clear(thread: ThreadContext) -> None:
        await thread.delete(PENDING_KEY)
