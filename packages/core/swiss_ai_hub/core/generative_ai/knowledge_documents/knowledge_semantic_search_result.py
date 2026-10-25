from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_semantic_match import KnowledgeSemanticMatch


class KnowledgeSemanticSearchResult(BaseModel):
    """One page of documents ranked by meaning, out of every document in scope.

    Unlike a content search, a ranking is not a filter: every document in scope with an indexed passage has a place in
    it, so `documents_in_scope` tells a caller how far down the ranking it could still read.
    """

    matches: Annotated[list[KnowledgeSemanticMatch], Field(description="Ranked documents on this page, best first")]
    documents_in_scope: Annotated[int, Field(description="Fully ingested documents the ranking was drawn from")]
    next_offset: Annotated[
        int | None, Field(description="Offset of the next page, or None when the ranking ends with this page")
    ]
