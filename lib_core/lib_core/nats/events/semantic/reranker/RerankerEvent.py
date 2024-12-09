from typing import Optional, List, Dict
from pydantic import Field

from openinference.semconv.trace import (
    RerankerAttributes,
    SpanAttributes,
    OpenInferenceSpanKindValues,
)

from lib_core.nats.events.semantic.SemanticEvent import SemanticEvent
from lib_core.nats.events.semantic.retriever.RetrieverEvent import Document


class RerankerEvent(SemanticEvent):
    input_documents: Optional[List[Document]] = Field(
        None, description="List of input documents provided to the reranker."
    )
    output_documents: Optional[List[Document]] = Field(None, description="List of documents outputted by the reranker.")
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
        if self.input_documents:
            for i, doc in enumerate(self.input_documents):
                attributes = {
                    **attributes,
                    **doc.to_semantic_convention(RerankerAttributes.RERANKER_INPUT_DOCUMENTS, i),
                }

        # Flatten output documents
        if self.output_documents:
            for i, doc in enumerate(self.output_documents):
                attributes = {
                    **attributes,
                    **doc.to_semantic_convention(RerankerAttributes.RERANKER_OUTPUT_DOCUMENTS, i),
                }

        return attributes
