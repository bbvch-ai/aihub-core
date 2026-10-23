from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.generative_ai import ExtractedTableMarkup


class ExtractionHistory:
    """A conversation with the tables of earlier answers replaced by a line each.

    Chat clients send every earlier answer back with each message, and the API and the pipe condense tables on the
    way in; a blueprint offering extraction condenses again, since its history can come from any client.
    """

    @staticmethod
    def condensed(messages: list[ChatMessage]) -> list[ChatMessage]:
        return [ExtractionHistory._condensed(message) for message in messages]

    @staticmethod
    def _condensed(message: ChatMessage) -> ChatMessage:
        if message.role != MessageRole.ASSISTANT or not message.content:
            return message
        condensed = ExtractedTableMarkup.condensed(message.content)
        if condensed == message.content:
            return message
        return ChatMessage(role=message.role, content=condensed, additional_kwargs=message.additional_kwargs)
