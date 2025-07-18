from typing import Annotated

from openinference.semconv.trace import EmbeddingAttributes, SpanAttributes
from pydantic import BaseModel, Field


class Embedding(BaseModel):
    text: Annotated[str | None, Field(description="The text represented by the embedding.")] = None
    vector: Annotated[list[float] | None, Field(description="The embedding vector as a list of floats.")] = None

    def to_semantic_convention(self, i: int) -> dict[str, str]:
        return {
            f"{SpanAttributes.EMBEDDING_EMBEDDINGS}.{i}.{EmbeddingAttributes.EMBEDDING_TEXT}": self.text,
            f"{SpanAttributes.EMBEDDING_EMBEDDINGS}.{i}.{EmbeddingAttributes.EMBEDDING_VECTOR}": self.vector,
        }
