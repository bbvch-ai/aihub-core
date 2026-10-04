from typing import Annotated, ClassVar

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field

from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class ContextualizeConversationEvent(ControlAndDisplayEvent):
    """
    Asks the conversation capability to turn a limited chat history into a contextualized turn: inspect the
    message for a meta question, derive the query the turn is answered for, and title the thread.

    Built with `Conversation.contextualize(...)`; answered with `ConversationContextualizedEvent`, or with a
    stop event when the message was a meta question or could not be condensed.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.contextualize_conversation_event.name"
    )
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.contextualize_conversation_event.description"
    )

    history: Annotated[list[ChatMessage], Field(description="The chat history, already limited to the budget.")]
    user_query: Annotated[
        str | None,
        Field(
            description="The raw text of the user's message, inspected for a meta question. None for a "
            "programmatic start, which skips inspection."
        ),
    ] = None
