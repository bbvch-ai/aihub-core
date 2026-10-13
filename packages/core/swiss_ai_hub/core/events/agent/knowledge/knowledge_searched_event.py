from typing import Annotated, ClassVar

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field

from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent
from swiss_ai_hub.core.events.agent.user.knowledge_reference import KnowledgeReference
from swiss_ai_hub.core.generative_ai.document.types.ingested_node import IngestedNode
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class KnowledgeSearchedEvent(ControlAndDisplayEvent):
    """
    The answer to `SearchKnowledgeEvent`: one context block with what the referenced collections hold for the query.

    Displayed because `grounding_nodes` are the documents the model is handed, so a chat client lists and numbers
    exactly the sources the answer can cite, as it does for a knowledge agent's own retrieval.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.knowledge_searched_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.knowledge_searched_event.description"
    )

    block: Annotated[
        list[ChatMessage], Field(description="System messages carrying the documents found, or none.")
    ] = []
    grounding_nodes: Annotated[
        list[IngestedNode], Field(description="The document sections the block holds, for listing as sources.")
    ] = []
    refused: Annotated[
        list[KnowledgeReference],
        Field(description="Referenced collections that were not searched, because the user may not read them."),
    ] = []
    tool_call_id: Annotated[
        str | None,
        Field(description="The tool call this answers when the model chose the search in a tool loop; none otherwise."),
    ] = None
