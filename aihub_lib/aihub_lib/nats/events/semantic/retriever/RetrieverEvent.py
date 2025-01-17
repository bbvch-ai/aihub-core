from typing import Dict, List, Optional

from llama_index.core.schema import NodeWithScore
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes
from pydantic import Field

from aihub_lib.nats.events.semantic.retriever.Document import Document
from aihub_lib.nats.events.semantic.SemanticEvent import SemanticEvent


class RetrieverEvent(SemanticEvent):
    documents: Optional[List[Document]] = Field(
        None,
        description="List of documents retrieved by the retriever, including document IDs, scores, and content.",
    )

    def to_semantic_convention(self) -> Dict[str, str]:
        attributes = {
            SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.RETRIEVER.value,
        }

        # Flatten retrieved documents
        if self.documents:
            for i, doc in enumerate(self.documents):
                attributes = {
                    **attributes,
                    **doc.to_semantic_convention(SpanAttributes.RETRIEVAL_DOCUMENTS, i),
                }

        return attributes

    @classmethod
    def from_nodes(cls, nodes: List[NodeWithScore]) -> "RetrieverEvent":
        documents = [Document.from_node(node) for node in nodes]
        return cls(documents=documents)
