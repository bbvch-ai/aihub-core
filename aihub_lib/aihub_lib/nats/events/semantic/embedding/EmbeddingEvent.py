from typing import Dict, List, Optional, ClassVar

from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes
from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.semantic.embedding.Embedding import Embedding
from aihub_lib.nats.events.semantic.SemanticEvent import SemanticEvent


class EmbeddingEvent(SemanticEvent):
    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.semantic_embedding_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.semantic_embedding_event.description")

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

        return {k: v for k, v in attributes.items() if v is not None}
