import json
from typing import Annotated, Any, ClassVar

from llama_index.core.base.llms.types import ChatMessage
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes
from pydantic import Field

from swiss_ai_hub.core.events.agent.semantic.semantic_event import SemanticEvent
from swiss_ai_hub.core.events.agent.web_fetch.web_fetch_failure import WebFetchFailure
from swiss_ai_hub.core.events.agent.web_search.web_search_result import WebSearchResult
from swiss_ai_hub.core.generative_ai.document.types.ingested_node import IngestedNode
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class WebSearchedEvent(SemanticEvent):
    """
    The answer to `SearchWebEvent`: the hits, and one context block with the pages read and the snippets of the rest.

    `results` is what a chat client lists as the sites searched; `grounding_nodes` are what the model is handed, one
    per hit, so a client lists exactly the sources the answer can cite. A semantic event, so the search shows in the
    trace as a retrieval of those hits, with the queries and the pages that could not be read beside them.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.web_searched_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.web_searched_event.description"
    )

    queries: Annotated[list[str], Field(description="The queries that were searched.")] = []
    results: Annotated[list[WebSearchResult], Field(description="The hits, best first, without duplicates.")] = []
    block: Annotated[
        list[ChatMessage], Field(description="System messages carrying the pages read and the other hits' snippets.")
    ] = []
    grounding_nodes: Annotated[
        list[IngestedNode], Field(description="The hits the block holds, one per hit, for listing as sources.")
    ] = []
    failures: Annotated[
        list[WebFetchFailure],
        Field(description="Hits whose page could not be read, so only their snippet was used."),
    ] = []
    unresponsive_engines: Annotated[
        list[str],
        Field(
            description="Search engines that did not answer, with SearXNG's reason (a CAPTCHA, a rate limit), so a "
            "search every engine refused does not read as one that matched nothing."
        ),
    ] = []
    tool_call_id: Annotated[
        str | None,
        Field(description="The tool call this answers when the model chose the search in a tool loop; none otherwise."),
    ] = None

    def to_semantic_convention(self) -> dict[str, Any]:
        attributes: dict[str, Any] = {
            SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.RETRIEVER.value,
            SpanAttributes.INPUT_VALUE: "\n".join(self.queries) or None,
        }
        for i, node in enumerate(self.grounding_nodes):
            attributes.update(node.to_semantic_convention(SpanAttributes.RETRIEVAL_DOCUMENTS, i))
        metadata = {
            "failures": [failure.model_dump(mode="json") for failure in self.failures],
            "unresponsive_engines": self.unresponsive_engines,
        }
        if any(metadata.values()):
            attributes[SpanAttributes.METADATA] = json.dumps({key: value for key, value in metadata.items() if value})
        return {key: value for key, value in attributes.items() if value is not None}
