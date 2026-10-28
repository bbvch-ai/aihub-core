from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class FetchWebPagesEvent(ControlAndDisplayEvent):
    """
    Asks the web fetch capability to read the pages the user linked, pasted in the message or referenced with `#`.

    Built with `WebFetch.fetch(...)`; answered with `WebPagesFetchedEvent`, empty when fetching is off for the
    profile. The URLs are passed as the user sent them, so a malformed one is reported back rather than dropped.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.fetch_web_pages_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.fetch_web_pages_event.description"
    )

    urls: Annotated[list[str], Field(description="The links to read, in the order the user gave them.")] = []
    reading: Annotated[
        bool,
        Field(
            description="Whether the pages are read: false while the profile has web fetch off, so a chat client "
            "shows no reading progress for links that are left unread."
        ),
    ] = True
    cite_sources: Annotated[
        bool,
        Field(description="Whether the model is told to cite the pages by id, off where citations cannot resolve."),
    ] = True
    tool_call_id: Annotated[
        str | None,
        Field(description="The tool call this answers when the model chose the fetch in a tool loop; none otherwise."),
    ] = None
