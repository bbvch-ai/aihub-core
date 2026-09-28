from typing import Annotated

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field, field_validator
from swiss_ai_hub.core.events.agent import ControlEvent


class FewShotStandaloneQuestionCondenserEvent(ControlEvent):
    """
    Event to condense chat messages into a single standalone question as a chat message.
    """

    condensed_chat_message: Annotated[
        ChatMessage, Field(description="Single chat message containing the condensed user question.")
    ]

    @field_validator("condensed_chat_message")
    @classmethod
    def _reject_blank_question(cls, message: ChatMessage) -> ChatMessage:
        """A blank question is worse here than in the RAG agents, not milder.

        `create_few_shot_examples` deliberately drops the chat history and the original user message from
        the final prompt — the condensed question is the sole carrier of what was asked. An empty one leaves
        the model classifying nothing, so the provider rejects the turn or the model answers a question that
        was never posed.

        Duplicated from `StandaloneQuestionCondenserEvent` rather than inherited: the two events have
        different bases (`ControlEvent` vs `ControlAndDisplayEvent`), so there is no shared ancestor to hang
        this on.
        """
        if not (message.content or "").strip():
            raise ValueError(
                "condensed_chat_message must carry a non-blank question — it is the only carrier of the "
                "user's question in the few-shot prompt"
            )
        return message

    @property
    def condensed_question(self) -> str:
        """The condensed question, guaranteed non-blank by the validator above."""
        return (self.condensed_chat_message.content or "").strip()
