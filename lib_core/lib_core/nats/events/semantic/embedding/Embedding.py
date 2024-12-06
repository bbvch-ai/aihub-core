from typing import Optional, List

from openinference.semconv.trace import SpanAttributes, EmbeddingAttributes
from pydantic import BaseModel, Field


class Embedding(BaseModel):
    text: Optional[str] = Field(None, description="The text represented by the embedding.")
    vector: Optional[List[float]] = Field(None, description="The embedding vector as a list of floats.")

    def to_semantic_convention(self, i: int) -> dict:
        return {
            f"{SpanAttributes.EMBEDDING_EMBEDDINGS}.{i}.{EmbeddingAttributes.EMBEDDING_TEXT}": self.text,
            f"{SpanAttributes.EMBEDDING_EMBEDDINGS}.{i}.{EmbeddingAttributes.EMBEDDING_VECTOR}": self.vector,
        }