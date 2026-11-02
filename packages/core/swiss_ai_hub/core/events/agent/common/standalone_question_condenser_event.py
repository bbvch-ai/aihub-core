from typing import Annotated, ClassVar

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field

from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class StandaloneQuestionCondenserEvent(ControlAndDisplayEvent):
    """
    Event to condense chat messages into a single standalone question as a chat message.
    """

    # No blank-question validator on purpose: `condense_standalone_question` already refuses blanks, and a
    # validator would also run when replay and the thread timeline read back older, pre-fix blank events.
    # See ADR 2026_09_07_memory_operations_use_condensed_question.

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.standalone_question_condenser_event.name"
    )
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.standalone_question_condenser_event.description"
    )
    condensed_chat_message: Annotated[
        ChatMessage, Field(description="Single chat message containing the condensed user question.")
    ]

    @property
    def condensed_question(self) -> str:
        """Non-blank for anything this deployment publishes; historical events may still be empty."""
        return (self.condensed_chat_message.content or "").strip()
