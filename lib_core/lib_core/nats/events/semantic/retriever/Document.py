import json
from typing import Optional
from pydantic import BaseModel, Field

from openinference.semconv.trace import DocumentAttributes


class Document(BaseModel):
    id: str = Field(..., description="Unique identifier for the document.")
    score: Optional[float] = Field(None, description="Score representing the relevance of the document.")
    content: Optional[str] = Field(None, description="Content of the document.")
    metadata: Optional[dict] = Field(
        None,
        description="Optional metadata associated with the document as a dictionary."
    )

    def to_semantic_convention(self, key: str, i: int) -> dict:
        return {
            f"{key}.{i}.{DocumentAttributes.DOCUMENT_ID}": self.id,
            f"{key}.{i}.{DocumentAttributes.DOCUMENT_SCORE}": self.score,
            f"{key}.{i}.{DocumentAttributes.DOCUMENT_CONTENT}": self.content,
            f"{key}.{i}.{DocumentAttributes.DOCUMENT_METADATA}": json.dumps(self.metadata),
        }