from typing import Annotated, Any

from pydantic import Field
from swiss_ai_hub.core.form.form import Form

from swiss_ai_hub.agent.capabilities.web_search.web_search_config import WebSearchConfig


class WebSearchFields(Form):
    """The web search setting a blueprint's config gains by listing this mixin as a base.

    `WebSearch` annotates its steps with this class. Off unless the profile turns it on, for stored profiles and new
    ones alike: a search sends words from the conversation to search engines outside the platform. While it is off,
    the profile shows no Web Search toggle in chat clients.
    """

    web_search: Annotated[
        WebSearchConfig | None,
        Field(
            description="Search the web when the user switches on Web Search in the chat, and answer from the hits. "
            "Off, the profile shows no Web Search toggle.",
            title="Web Search",
        ),
    ] = None

    def web_search_reserve(self) -> int:
        """Tokens a blueprint keeps free for one search's hits; none while searching is off."""
        return self.web_search.context_reserve() if self.web_search else 0

    @classmethod
    def web_search_form_elements(cls) -> dict[str, Any]:
        """The form elements for this class's own fields, for a subclass's `as_form()` to spread."""
        return {"web_search": WebSearchConfig.as_form()}
