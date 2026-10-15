from typing import Annotated, Any

from pydantic import Field
from swiss_ai_hub.core.form.form import Form

from swiss_ai_hub.agent.capabilities.web_fetch.web_fetch_config import WebFetchConfig


class WebFetchFields(Form):
    """The web fetch setting a blueprint's config gains by listing this mixin as a base.

    `WebFetch` annotates its steps with this class. Off unless the profile turns it on, for stored profiles and new
    ones alike: reading a link sends a request from the platform to a site the user chose.
    """

    web_fetch: Annotated[
        WebFetchConfig | None,
        Field(
            description="Read the web pages a message links, pasted or referenced with #, and answer from them. "
            "Off, links are left alone.",
            title="Read Linked Web Pages",
        ),
    ] = None

    def web_fetch_reserve(self, links: list[str]) -> int:
        """Tokens a blueprint keeps free for the pages these links lead to; none while fetching is off."""
        return self.web_fetch.context_reserve(len(links)) if self.web_fetch and links else 0

    @classmethod
    def web_fetch_form_elements(cls) -> dict[str, Any]:
        """The form elements for this class's own fields, for a subclass's `as_form()` to spread."""
        return {"web_fetch": WebFetchConfig.as_form()}
