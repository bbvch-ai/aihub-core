from typing import Annotated

from pydantic import BaseModel, Field, computed_field

from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_content_match import KnowledgeContentMatch


class KnowledgeContentSearchResult(BaseModel):
    """One page of the documents a content search matched.

    Searching again with `next_offset` until it is None returns every matching document exactly once, whatever the
    page size, which is what makes the search exhaustive rather than a top-k.
    """

    matches: Annotated[list[KnowledgeContentMatch], Field(description="Matching documents on this page")]
    total_documents: Annotated[
        int,
        Field(
            description="Matching documents across all pages: those the database matched, less any this call found "
            "no matching line in, which only happens where the database's regex dialect is looser than Python's"
        ),
    ]
    next_offset: Annotated[int | None, Field(description="Offset of the next page, or None on the last page")]

    @computed_field
    @property
    def truncated(self) -> bool:
        return self.next_offset is not None
