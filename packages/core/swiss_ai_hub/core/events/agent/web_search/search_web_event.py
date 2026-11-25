from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class SearchWebEvent(ControlAndDisplayEvent):
    """
    Asks the web search capability to search the web for the given queries and read the best hits.

    Built with `WebSearch.search(...)` or from the model's `search_web` tool call; answered with `WebSearchedEvent`.
    Displayed with its queries, so a chat client can show what is being searched for while the search runs.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.search_web_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.search_web_event.description"
    )

    queries: Annotated[list[str], Field(description="The search queries, each sent to the search engines.")] = []
    searching: Annotated[
        bool,
        Field(
            description="Whether the search runs: false while the profile has web search off or the user's Web "
            "Search toggle is, so a chat client shows no search progress."
        ),
    ] = True
    cite_sources: Annotated[
        bool,
        Field(description="Whether the model is told to cite the hits by id, off where citations cannot resolve."),
    ] = True
    tool_call_id: Annotated[
        str | None,
        Field(description="The tool call this answers when the model chose the search in a tool loop; none otherwise."),
    ] = None
