import json
from typing import Annotated, Any, ClassVar

from llama_index.core.base.llms.types import ChatMessage
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes
from pydantic import Field

from swiss_ai_hub.core.events.agent.semantic.semantic_event import SemanticEvent
from swiss_ai_hub.core.events.agent.web_fetch.web_fetch_failure import WebFetchFailure
from swiss_ai_hub.core.generative_ai.document.types.ingested_node import IngestedNode
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class WebPagesFetchedEvent(SemanticEvent):
    """
    The answer to `FetchWebPagesEvent`: one context block with the pages that were read, and the links that were not.

    Displayed because `grounding_nodes` are the pages the model is handed, so a chat client lists exactly the sources
    the answer can cite, by title and URL. A semantic event, so the fetch step shows in the trace as a retrieval of
    those pages, with the failures beside them.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.web_pages_fetched_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.web_pages_fetched_event.description"
    )

    block: Annotated[
        list[ChatMessage], Field(description="System messages carrying the pages read and the links that failed.")
    ] = []
    grounding_nodes: Annotated[
        list[IngestedNode], Field(description="The pages the block holds, one per page, for listing as sources.")
    ] = []
    failures: Annotated[
        list[WebFetchFailure], Field(description="The links that could not be read, with the reason for each.")
    ] = []
    tool_call_id: Annotated[
        str | None,
        Field(description="The tool call this answers when the model chose the fetch in a tool loop; none otherwise."),
    ] = None

    def to_semantic_convention(self) -> dict[str, Any]:
        attributes: dict[str, Any] = {
            SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.RETRIEVER.value,
        }
        for i, node in enumerate(self.grounding_nodes):
            attributes.update(node.to_semantic_convention(SpanAttributes.RETRIEVAL_DOCUMENTS, i))
        if self.failures:
            attributes[SpanAttributes.METADATA] = json.dumps(
                {"failures": [failure.model_dump(mode="json") for failure in self.failures]}
            )
        return {key: value for key, value in attributes.items() if value is not None}
