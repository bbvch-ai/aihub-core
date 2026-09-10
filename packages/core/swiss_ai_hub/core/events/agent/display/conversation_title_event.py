from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.display.display_event import DisplayEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class ConversationTitleEvent(DisplayEvent):
    """
    Carries a generated title for the whole conversation (thread), produced by the agent once a
    topic becomes identifiable. The agent has the richest context about the conversation, so it
    owns this metadata instead of leaving it to the chat UI's task model.

    A thread receives a single, stable title: the agent emits this event only on the turn where a
    title is first determined and never again for that thread.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.conversation_title_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.conversation_title_event.description"
    )

    title: Annotated[str, Field(description="The generated title for the conversation.")]
