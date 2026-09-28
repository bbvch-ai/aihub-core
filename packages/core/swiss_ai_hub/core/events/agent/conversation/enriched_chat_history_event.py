from typing import Annotated

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field

from swiss_ai_hub.core.events.agent.control.control_event import ControlEvent


class EnrichedChatHistoryEvent(ControlEvent):
    """
    The limited chat history with every installed enricher's context blocks merged in, re-limited to the
    model's input budget.

    This is the history a blueprint's answer pipeline consumes. It is emitted once per turn, also when no
    enricher contributed anything, so the answer pipeline never has to fall back to the bare limited history.
    """

    extended_history: Annotated[
        list[ChatMessage],
        Field(description="Limited chat history extended with the context blocks of every enricher."),
    ]
