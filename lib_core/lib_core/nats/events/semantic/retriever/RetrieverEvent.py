from typing import Optional, List
from pydantic import Field

from openinference.semconv.trace import SpanAttributes, OpenInferenceSpanKindValues

from lib_core.nats.events.semantic import SemanticEvent
from lib_core.nats.events.semantic.retriever.Document import Document


class RetrieverEvent(SemanticEvent):
    documents: Optional[List[Document]] = Field(
        None,
        description="List of documents retrieved by the retriever, including document IDs, scores, and content."
    )

    def to_semantic_convention(self) -> dict:
        attributes = {
            SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.RETRIEVER.value,
        }

        # Flatten retrieved documents
        if self.documents:
            for i, doc in enumerate(self.documents):
                attributes = {
                    **attributes,
                    **doc.to_semantic_convention(SpanAttributes.RETRIEVAL_DOCUMENTS, i)
                }

        return attributes
