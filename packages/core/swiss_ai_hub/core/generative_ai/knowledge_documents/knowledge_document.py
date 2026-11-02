from typing import Annotated, Self

from pydantic import BaseModel, Field

from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_summary import KnowledgeDocumentSummary
from swiss_ai_hub.core.generative_ai.knowledge_documents.resolved_knowledge_collection import (
    ResolvedKnowledgeCollection,
)
from swiss_ai_hub.core.persistence.rag.documents.entities.ref_doc import RefDoc


class KnowledgeDocument(BaseModel):
    """A document's parsed text, whole or one character range of it.

    The text is kept apart from the summary so a caller can hand it to a model as untrusted content, and
    `text_length` always reports the full length so a caller reading in ranges knows when it has reached the end.
    """

    summary: Annotated[KnowledgeDocumentSummary, Field(description="The document's listing entry")]
    text: Annotated[str, Field(description="Parsed text from `start` up to `end`")]
    text_length: Annotated[int, Field(description="Length of the document's full parsed text in characters")]
    start: Annotated[int, Field(description="Offset of the first character of `text` in the full text")]
    end: Annotated[int, Field(description="Offset one past the last character of `text` in the full text")]

    @classmethod
    def from_ref_doc(
        cls,
        ref_doc: RefDoc,
        resolved: ResolvedKnowledgeCollection,
        start: int | None = None,
        end: int | None = None,
    ) -> Self:
        full_text = ref_doc.data.text or ""
        range_start, range_end, _ = slice(start, end).indices(len(full_text))
        range_end = max(range_start, range_end)
        return cls(
            summary=KnowledgeDocumentSummary.from_ref_doc(ref_doc, resolved),
            text=full_text[range_start:range_end],
            text_length=len(full_text),
            start=range_start,
            end=range_end,
        )
