from typing import Dict, List, Optional, ClassVar

from llama_index.core.schema import NodeWithScore
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes
from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.semantic.retriever.Document import Document
from aihub_lib.nats.events.semantic.SemanticEvent import SemanticEvent


class RetrieverEvent(SemanticEvent):
    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.semantic_retriever_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.semantic_retriever_event.description")

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

        return {k: v for k, v in attributes.items() if v is not None}

    @classmethod
    def from_nodes(cls, nodes: List[NodeWithScore]) -> "RetrieverEvent":
        documents = [Document.from_node(node) for node in nodes]
        return cls(documents=documents)
