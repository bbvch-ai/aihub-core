from typing import Annotated, Any, Self

from pydantic import BaseModel, Field

from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import DOCUMENT_ID


class DocumentPassageHit(BaseModel):
    """One passage a search grouped by document returned: which document, what it says and how close it is."""

    document_id: Annotated[str, Field(description="Document the passage was chunked or summarised from")]
    text: Annotated[str, Field(description="The passage's text")]
    score: Annotated[float, Field(description="Similarity to the query; inner product, so higher is closer")]

    @classmethod
    def from_hit(cls, hit: dict[str, Any], text_key: str) -> Self:
        entity = hit["entity"]
        return cls(document_id=entity[DOCUMENT_ID], text=entity.get(text_key) or "", score=hit["distance"])
