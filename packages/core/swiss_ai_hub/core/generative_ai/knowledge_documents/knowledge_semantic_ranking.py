from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_semantic_match import KnowledgeSemanticMatch


class KnowledgeSemanticRanking(BaseModel):
    """The documents in scope ordered by meaning, and how much of the scope that order covers.

    A ranking is not a filter, so a caller needs to know what it leaves out: documents beyond the cut (`capped`) and
    documents that have no indexed passage to be ranked by (`unranked`), which only a listing or a content search finds.
    """

    matches: Annotated[
        list[KnowledgeSemanticMatch],
        Field(description="Ranked documents, best first, merged across embedding models by reciprocal rank fusion"),
    ]
    documents_in_scope: Annotated[int, Field(description="Fully ingested documents the ranking was drawn from")]
    unranked: Annotated[int, Field(description="Documents in scope without any indexed passage, so never ranked")]
    capped: Annotated[
        bool, Field(description="Whether more documents had passages than the ranking holds, so it was cut")
    ]
