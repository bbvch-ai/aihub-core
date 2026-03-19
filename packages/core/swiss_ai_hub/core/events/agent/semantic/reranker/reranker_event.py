from typing import Annotated, ClassVar, Self

from llama_index.core.schema import NodeWithScore
from openinference.semconv.trace import OpenInferenceSpanKindValues, RerankerAttributes, SpanAttributes
from pydantic import Field

from swiss_ai_hub.core.events.agent.semantic.semantic_event import SemanticEvent
from swiss_ai_hub.core.generative_ai.document.types.ingested_node import IngestedNode
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class RerankerEvent(SemanticEvent):
    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.semantic_reranker_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.semantic_reranker_event.description"
    )

    input_nodes: Annotated[
        list[IngestedNode] | None, Field(description="List of input documents provided to the reranker.")
    ] = None
    output_nodes: Annotated[
        list[IngestedNode] | None, Field(description="List of documents outputted by the reranker.")
    ] = None
    query: Annotated[str | None, Field(description="The query string used by the reranker.")] = None
    rerank_model_name: Annotated[str | None, Field(description="Name of the reranker model being used.")] = None
    top_n: Annotated[
        int | None,
        Field(
            description="The top N parameter, representing the number of results to be reranked.",
        ),
    ] = None
    reranked: Annotated[bool | None, Field(description="Whether the nodes were reranked or not.")] = None

    def to_semantic_convention(self) -> dict[str, str]:
        attributes = {
            SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.RERANKER.value,
            RerankerAttributes.RERANKER_QUERY: self.query,
            RerankerAttributes.RERANKER_MODEL_NAME: self.rerank_model_name,
            RerankerAttributes.RERANKER_TOP_K: self.top_n,
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

    @classmethod
    def from_nodes(cls, nodes: list[NodeWithScore]) -> Self:
        return cls(output_nodes=nodes)
