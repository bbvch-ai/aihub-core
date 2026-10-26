from typing import Annotated

from pydantic import BaseModel, Field


class KnowledgeSemanticPassage(BaseModel):
    """One indexed chunk of a document that a semantic search matched, as the vector index stores it."""

    text: Annotated[str, Field(description="The chunk's text")]
    score: Annotated[float, Field(description="Similarity to the query, higher is closer")]
