from typing import Optional, List, Dict
from pydantic import Field

from openinference.semconv.trace import SpanAttributes, OpenInferenceSpanKindValues

from lib_core.nats.events.semantic.SemanticEvent import SemanticEvent
from lib_core.nats.events.semantic.embedding.Embedding import Embedding


class EmbeddingEvent(SemanticEvent):
    text: Optional[str] = Field(None, description="The text represented in the embedding")
    embedding_model_name: Optional[str] = Field(None, description="The name of the embedding model used.")
    embeddings: Optional[List[Embedding]] = Field(
        None, description="A list of embedding objects containing text and vector data."
    )

    def to_semantic_convention(self) -> Dict[str, str]:
        attributes = {
            SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.EMBEDDING.value,
            SpanAttributes.EMBEDDING_MODEL_NAME: self.embedding_model_name,
        }

        if self.embeddings:
            for i, embedding in enumerate(self.embeddings):
                attributes = {**attributes, **embedding.to_semantic_convention(i)}

        return attributes
