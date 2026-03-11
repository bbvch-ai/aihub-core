from typing import Annotated, ClassVar

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field

from swiss_ai_hub.core.events.agent.ControlAndDisplayEvent import ControlAndDisplayEvent
from swiss_ai_hub.core.i18n.LocaleString import LocaleString


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
