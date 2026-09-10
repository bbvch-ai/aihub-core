from typing import Annotated

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field
from swiss_ai_hub.core.events.agent import ControlEvent
from swiss_ai_hub.core.generative_ai import IngestedNode


class InOrderNodeCombinerEvent(ControlEvent):
    """
    Order the retrieved nodes by document source and combine them into a single chat message.
    """

    context_message: Annotated[
        ChatMessage, Field(description="The message including the context nodes information in order.")
    ]
    grounding_nodes: Annotated[
        list[IngestedNode] | None,
        Field(
            default=None,
            description="Nodes (fresh retrieval plus carried prior-turn nodes) that ground this turn's answer.",
        ),
    ] = None
