from typing import Annotated, ClassVar, Self

from llama_index.core.schema import NodeWithScore
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes
from pydantic import Field

from swiss_ai_hub.core.events.agent.semantic.SemanticEvent import SemanticEvent
from swiss_ai_hub.core.generative_ai.document.types.IngestedNode import IngestedNode
from swiss_ai_hub.core.i18n.LocaleString import LocaleString


class RetrieverEvent(SemanticEvent):
    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.semantic_retriever_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.semantic_retriever_event.description"
    )

    nodes: Annotated[
        list[IngestedNode] | None,
        Field(
            description="List of nodes retrieved by the retriever, including document IDs, scores, and content.",
        ),
    ] = None

    def to_semantic_convention(self) -> dict[str, str]:
        attributes = {
            SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.RETRIEVER.value,
        }

        # Flatten retrieved documents
        if self.nodes:
            for i, node in enumerate(self.nodes):
                attributes = {
                    **attributes,
                    **node.to_semantic_convention(SpanAttributes.RETRIEVAL_DOCUMENTS, i),
                }

        return {k: v for k, v in attributes.items() if v is not None}

    @classmethod
    def from_nodes(cls, nodes: list[NodeWithScore]) -> Self:
        nodes = [IngestedNode.from_llama_index_node_with_score(node) for node in nodes]
        return cls(nodes=nodes)
