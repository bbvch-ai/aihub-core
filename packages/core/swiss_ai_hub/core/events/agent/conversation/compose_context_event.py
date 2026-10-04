from typing import Annotated, ClassVar

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field

from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class ComposeContextEvent(ControlAndDisplayEvent):
    """
    Asks the conversation capability to merge context blocks into a chat history, in the given order, behind
    the leading system messages and within the input budget.

    Built with `Conversation.compose(...)`; answered with `ContextComposedEvent`.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.compose_context_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.compose_context_event.description"
    )

    history: Annotated[list[ChatMessage], Field(description="The chat history to merge the blocks into.")]
    blocks: Annotated[
        list[list[ChatMessage]],
        Field(description="Context blocks in the order they should reach the model. Empty blocks are skipped."),
    ] = []
