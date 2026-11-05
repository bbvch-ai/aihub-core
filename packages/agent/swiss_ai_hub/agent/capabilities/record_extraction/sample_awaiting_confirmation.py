from typing import Annotated, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.events.agent import ExtractRecordsEvent
from swiss_ai_hub.core.generative_ai import BucketNamespacePair, KnowledgeDocumentSelection, RecordSchema

from swiss_ai_hub.agent.context.thread.thread_context import ThreadContext

CONFIRMATION_KEY = "record_extraction:awaiting_confirmation"


class SampleAwaitingConfirmation(BaseModel):
    """A selection too large to extract unasked, whose sample the user was shown: what a "yes" extracts.

    It keeps the selection, not its documents, so a confirmation re-resolves it and counts documents added or removed
    since, and it keeps the columns, so the whole table has the sample's. Small and free of rows, it lives per
    conversation until the user confirms or asks something else, which replaces it.
    """

    extraction_id: Annotated[str, Field(description="The extraction that showed the sample.")]
    selection: Annotated[KnowledgeDocumentSelection, Field(description="The documents to extract from.")]
    collections: Annotated[list[BucketNamespacePair], Field(description="The collections the sample was taken from.")]
    record_schema: Annotated[RecordSchema, Field(description="The columns of the sample, kept for the whole table.")]
    fields: Annotated[str, Field(description="The columns in the user's words.")]
    instructions: Annotated[str | None, Field(description="Which records to keep.")] = None
    row_terms: Annotated[str | None, Field(description="What lines holding wanted records usually contain.")] = None
    document_terms: Annotated[str | None, Field(description="What documents holding wanted records contain.")] = None
    total_documents: Annotated[int, Field(description="Documents the selection held when sampled.", ge=0)] = 0
    cut_short: Annotated[bool, Field(description="Whether the search that chose the documents stopped early.")] = False
    notices: Annotated[list[str], Field(description="What the sampled answer told the user about its scope.")] = []

    @classmethod
    def of(cls, request: ExtractRecordsEvent, schema: RecordSchema, total_documents: int) -> Self:
        if request.selection is None:
            raise ValueError("only a new selection can be sampled")
        return cls(
            extraction_id=request.event_id,
            selection=request.selection,
            collections=request.collections,
            record_schema=schema,
            fields=request.fields,
            instructions=request.instructions,
            row_terms=request.row_terms,
            document_terms=request.document_terms,
            total_documents=total_documents,
            cut_short=request.cut_short,
            notices=request.notices,
        )

    def within(self, collections: list[BucketNamespacePair]) -> bool:
        """Whether every collection sampled from is still one the confirming run may read."""
        allowed = {(pair.bucket_name, pair.namespace_name) for pair in collections}
        return all((pair.bucket_name, pair.namespace_name) in allowed for pair in self.collections)

    def as_request(self, confirming: ExtractRecordsEvent) -> ExtractRecordsEvent:
        """The confirming request with the sampled selection, answering the confirming call and run; what the sample
        said about a search that stopped early still holds for the whole table."""
        return confirming.model_copy(
            update={
                "selection": self.selection,
                "fields": self.fields,
                "instructions": self.instructions,
                "row_terms": self.row_terms,
                "document_terms": self.document_terms,
                "collections": self.collections,
                "cut_short": confirming.cut_short or self.cut_short,
                "notices": list(dict.fromkeys([*confirming.notices, *self.notices])),
            }
        )

    @classmethod
    async def load(cls, thread: ThreadContext, agent_id: str) -> Self | None:
        """The sample this profile shows in the thread, left in place."""
        stored = await thread.get(SampleAwaitingConfirmation._key(agent_id))
        return cls.model_validate(stored) if stored else None

    @classmethod
    async def take(cls, thread: ThreadContext, agent_id: str) -> Self | None:
        """The sample this profile shows in the thread, removed in the same step, so two confirmations never both
        extract it."""
        stored = await thread.pop(SampleAwaitingConfirmation._key(agent_id))
        return cls.model_validate(stored) if stored else None

    async def save(self, thread: ThreadContext, agent_id: str) -> None:
        await thread.set(SampleAwaitingConfirmation._key(agent_id), self.model_dump(mode="json"))

    @staticmethod
    async def clear(thread: ThreadContext, agent_id: str) -> None:
        await thread.delete(SampleAwaitingConfirmation._key(agent_id))

    @staticmethod
    def _key(agent_id: str) -> str:
        """Per profile: several agents may share a thread, and one must not extract another's sample."""
        return f"{CONFIRMATION_KEY}:{agent_id}"
