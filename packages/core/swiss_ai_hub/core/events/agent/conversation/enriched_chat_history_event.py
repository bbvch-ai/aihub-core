from typing import Annotated, ClassVar

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field

from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class EnrichedChatHistoryEvent(ControlAndDisplayEvent):
    """
    The limited chat history with every installed enricher's context blocks merged in, re-limited to the
    model's input budget.

    This is the history a blueprint's answer pipeline consumes. It is emitted once per turn, also when no
    enricher contributed anything, so the answer pipeline never has to fall back to the bare limited history.
    Displayed because it is exactly what the model saw, which is the transparency the per-enricher display
    events cannot give on their own.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.enriched_chat_history_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.enriched_chat_history_event.description"
    )

    extended_history: Annotated[
        list[ChatMessage],
        Field(description="Limited chat history extended with the context blocks of every enricher."),
    ]
