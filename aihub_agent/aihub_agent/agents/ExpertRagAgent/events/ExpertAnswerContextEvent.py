from typing import Annotated

from aihub_lib.nats.events import ControlEvent
from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field


class ExpertAnswerContextEvent(ControlEvent):
    """
    Event carrying expert answer as context for LLM response generation.
    """

    context_message: Annotated[ChatMessage, Field(description="The expert answer formatted as a context message.")]
