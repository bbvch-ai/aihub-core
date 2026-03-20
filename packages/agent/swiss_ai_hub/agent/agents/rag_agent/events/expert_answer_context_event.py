from typing import Annotated

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field
from swiss_ai_hub.core.events.agent import ControlEvent


class ExpertAnswerContextEvent(ControlEvent):
    """
    Event carrying expert answer as context for LLM response generation.
    """

    context_message: Annotated[ChatMessage, Field(description="The expert answer formatted as a context message.")]
