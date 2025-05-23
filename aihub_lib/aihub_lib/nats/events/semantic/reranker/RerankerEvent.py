from typing import ClassVar, Dict, List, Optional

from openinference.semconv.trace import OpenInferenceSpanKindValues, RerankerAttributes, SpanAttributes
from pydantic import Field

from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.semantic.SemanticEvent import SemanticEvent


class RerankerEvent(SemanticEvent):
    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.semantic_reranker_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.semantic_reranker_event.description"
    )

    input_nodes: Optional[List[IngestedNode]] = Field(
        None, description="List of input documents provided to the reranker."
    )
    output_nodes: Optional[List[IngestedNode]] = Field(None, description="List of documents outputted by the reranker.")
    query: Optional[str] = Field(None, description="The query string used by the reranker.")
    rerank_model_name: Optional[str] = Field(None, description="Name of the reranker model being used.")
    top_k: Optional[int] = Field(
        None,
        description="The top K parameter, representing the number of results to be reranked.",
    )

    def to_semantic_convention(self) -> Dict[str, str]:
        attributes = {
            SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.RERANKER.value,
            RerankerAttributes.RERANKER_QUERY: self.query,
            RerankerAttributes.RERANKER_MODEL_NAME: self.rerank_model_name,
            RerankerAttributes.RERANKER_TOP_K: self.top_k,
        }

        # Flatten input documents
        if self.input_nodes:
            for i, node in enumerate(self.input_nodes):
                attributes = {
                    **attributes,
                    **node.to_semantic_convention(RerankerAttributes.RERANKER_INPUT_DOCUMENTS, i),
                }

        # Flatten output documents
        if self.output_nodes:
            for i, node in enumerate(self.output_nodes):
                attributes = {
                    **attributes,
                    **node.to_semantic_convention(RerankerAttributes.RERANKER_OUTPUT_DOCUMENTS, i),
                }

        return {k: v for k, v in attributes.items() if v is not None}
