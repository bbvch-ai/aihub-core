from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.display.display_event import DisplayEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class ConversationTagsEvent(DisplayEvent):
    """
    Carries category tags describing the conversation, produced by the agent. Tags are refreshed
    every turn so they track topic shifts over the course of the conversation.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.conversation_tags_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.conversation_tags_event.description"
    )

    tags: Annotated[list[str], Field(description="The category tags describing the conversation.")]
