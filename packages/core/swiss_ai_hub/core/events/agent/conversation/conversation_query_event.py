from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.events.agent.control.control_event import ControlEvent


class ConversationQueryEvent(ControlEvent):
    """
    The one query a conversational turn is answered for, released once the meta-question gate has cleared
    the message.

    Control-only: it exists so every step downstream of the entry point — enrichers, retrieval, memory
    storage — reads the same question, whether the spine condensed it out of the history or took the last
    user message as is. A blueprint that condenses also emits the display-facing
    `StandaloneQuestionCondenserEvent`, which is what the chat renders.
    """

    query: Annotated[
        str,
        Field(description="The question this turn is answered for. Blank when the message carried no text."),
    ]
    condensed: Annotated[
        bool,
        Field(description="Whether the query was condensed from the history rather than taken verbatim."),
    ] = False

    @property
    def is_blank(self) -> bool:
        return not self.query.strip()
