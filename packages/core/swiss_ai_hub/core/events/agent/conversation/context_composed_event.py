from typing import Annotated, ClassVar

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field

from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class ContextComposedEvent(ControlAndDisplayEvent):
    """
    The answer to `ComposeContextEvent`: the chat history with the requested context blocks merged in behind
    the leading system messages, re-limited to the model's input budget.

    Displayed because it is exactly what the model receives, which the per-capability display events cannot
    show on their own.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.context_composed_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.context_composed_event.description"
    )

    history: Annotated[
        list[ChatMessage],
        Field(description="Chat history with the context blocks merged in, within the input budget."),
    ]
