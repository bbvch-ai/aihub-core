from typing import Annotated

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field
from swiss_ai_hub.core.events.agent.control.ControlEvent import ControlEvent


class FewShotStandaloneQuestionCondenserEvent(ControlEvent):
    """
    Event to condense chat messages into a single standalone question as a chat message.
    """

    condensed_chat_message: Annotated[
        ChatMessage, Field(description="Single chat message containing the condensed user question.")
    ]
