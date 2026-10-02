from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.events.agent.control.control_event import ControlEvent
from swiss_ai_hub.core.events.agent.user.knowledge_reference import KnowledgeReference


class SearchKnowledgeEvent(ControlEvent):
    """
    Asks the knowledge capability to search the collections the user referenced for the turn's query.

    Built with `Knowledge.search(...)`; answered with `KnowledgeSearchedEvent`, empty when nothing was referenced.
    """

    references: Annotated[
        list[KnowledgeReference], Field(description="The collections the user referenced on this message.")
    ] = []
    query: Annotated[str, Field(description="The turn's query the collections are searched for.")] = ""
    cite_sources: Annotated[
        bool,
        Field(description="Whether the model is told to cite the documents by id, off where citations cannot resolve."),
    ] = True
