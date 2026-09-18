from typing import Annotated

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field
from swiss_ai_hub.core.events.agent import ControlEvent


class FewShotStandaloneQuestionCondenserEvent(ControlEvent):
    """
    Event to condense chat messages into a single standalone question as a chat message.

    A blank question matters more here than in the RAG agents: `create_few_shot_examples` drops the chat
    history and the original user message from the final prompt, so the condensed question is the sole
    carrier of what was asked. That is enforced where it can be acted on — `condense_standalone_question`
    raises before this event is built — and not as a `field_validator`, which would also run on JetStream
    replay and make pre-existing blank events undeserializable. See `StandaloneQuestionCondenserEvent`.
    """

    condensed_chat_message: Annotated[
        ChatMessage, Field(description="Single chat message containing the condensed user question.")
    ]

    @property
    def condensed_question(self) -> str:
        """Non-blank for anything this deployment publishes; historical events may still be empty."""
        return (self.condensed_chat_message.content or "").strip()
