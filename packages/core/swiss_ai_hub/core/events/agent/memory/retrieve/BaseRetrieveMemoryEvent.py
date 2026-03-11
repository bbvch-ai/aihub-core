from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.ControlAndDisplayEvent import ControlAndDisplayEvent
from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.infrastructure.mem0.types.Memory import Memory
from swiss_ai_hub.core.infrastructure.mem0.types.MemoryRelation import MemoryRelation
from swiss_ai_hub.core.infrastructure.mem0.types.MemorySearchResult import MemorySearchResult


class BaseRetrieveMemoryEvent(ControlAndDisplayEvent):
    """
    A control and display event emitted when an agent retrieves memories from long-term storage.

    ### Why BaseRetrieveMemoryEvent?
    This event bridges the gap between stateless conversation and stateful user context:
    - As a control event, it provides retrieved memories to downstream workflow steps
    - As a display event, it shows users what context the agent is using from past interactions

    Agents emit this event after semantic search through user/organization memories. The retrieved
    memories are then typically prepended to chat history as system context, enabling personalized
    responses. This transparency is crucial for user trust - they can see what the agent "remembers"
    and correct inaccuracies if needed.

    The event includes both individual memories and their relations in the knowledge graph, allowing
    agents to understand not just isolated facts but how concepts connect.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.retrieve_memory_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.retrieve_memory_event.description"
    )
    memories: Annotated[list[Memory], Field(description="The list of memories that were retrieved.")] = []
    relations: Annotated[list[MemoryRelation], Field(description="The list of matching memory relations.")]

    @classmethod
    def from_memory_search_result(cls, memory_search_result: MemorySearchResult):
        return cls(memories=memory_search_result.results, relations=memory_search_result.relations)
