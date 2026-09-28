from typing import Annotated, ClassVar

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field, field_validator

from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class StandaloneQuestionCondenserEvent(ControlAndDisplayEvent):
    """
    Event to condense chat messages into a single standalone question as a chat message.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.standalone_question_condenser_event.name"
    )
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.standalone_question_condenser_event.description"
    )
    condensed_chat_message: Annotated[
        ChatMessage, Field(description="Single chat message containing the condensed user question.")
    ]

    @field_validator("condensed_chat_message")
    @classmethod
    def _reject_blank_question(cls, message: ChatMessage) -> ChatMessage:
        """Every consumer treats this as the turn's only question, so an empty one must not exist.

        Enforced on the event rather than only at the condenser because events are deserialized on
        JetStream replay and redelivery, where no step body runs. A length constraint cannot express this —
        the field is a llama-index `ChatMessage`, so the check has to reach `.content`.
        """
        if not (message.content or "").strip():
            raise ValueError(
                "condensed_chat_message must carry a non-blank question — it is what retrieval and memory "
                "search embed, and what an expert escalation asks a human"
            )
        return message

    @property
    def condensed_question(self) -> str:
        """The condensed question, guaranteed non-blank by the validator above."""
        return (self.condensed_chat_message.content or "").strip()
