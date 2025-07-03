from typing import Annotated

from aihub_lib.nats.events import ControlEvent
from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field


class InOrderNodeCombinerEvent(ControlEvent):
    """
    Order the retrieved nodes by document source and combine them into a single chat message.
    """

    context_message: Annotated[
        ChatMessage, Field(description="The message including the context nodes information in order.")
    ]
