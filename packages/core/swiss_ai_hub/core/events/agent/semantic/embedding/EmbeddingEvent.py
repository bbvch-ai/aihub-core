from typing import Annotated, ClassVar

from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes
from pydantic import Field

from swiss_ai_hub.core.events.agent.semantic.embedding.Embedding import Embedding
from swiss_ai_hub.core.events.agent.semantic.SemanticEvent import SemanticEvent
from swiss_ai_hub.core.i18n.LocaleString import LocaleString


class EmbeddingEvent(SemanticEvent):
    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.semantic_embedding_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.semantic_embedding_event.description"
    )

    text: Annotated[str | None, Field(description="The text represented in the embedding")] = None
    embedding_model_name: Annotated[str | None, Field(description="The name of the embedding model used.")] = None
    embeddings: Annotated[
        list[Embedding] | None, Field(description="A list of embedding objects containing text and vector data.")
    ] = None

    def to_semantic_convention(self) -> dict[str, str]:
        attributes = {
            SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.EMBEDDING.value,
            SpanAttributes.EMBEDDING_MODEL_NAME: self.embedding_model_name,
        }

        if self.embeddings:
            for i, embedding in enumerate(self.embeddings):
                attributes = {**attributes, **embedding.to_semantic_convention(i)}

        return {k: v for k, v in attributes.items() if v is not None}
