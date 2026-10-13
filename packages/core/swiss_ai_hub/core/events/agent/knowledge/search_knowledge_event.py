from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent
from swiss_ai_hub.core.events.agent.user.knowledge_reference import KnowledgeReference
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class SearchKnowledgeEvent(ControlAndDisplayEvent):
    """
    Asks the knowledge capability to search the collections the user referenced for the turn's query.

    Built with `Knowledge.search(...)`; answered with `KnowledgeSearchedEvent`, empty when nothing was referenced.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.search_knowledge_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.search_knowledge_event.description"
    )

    references: Annotated[
        list[KnowledgeReference], Field(description="The collections the user referenced on this message.")
    ] = []
    query: Annotated[str, Field(description="The turn's query the collections are searched for.")] = ""
    cite_sources: Annotated[
        bool,
        Field(description="Whether the model is told to cite the documents by id, off where citations cannot resolve."),
    ] = True
    tool_call_id: Annotated[
        str | None,
        Field(description="The tool call this answers when the model chose the search in a tool loop; none otherwise."),
    ] = None
