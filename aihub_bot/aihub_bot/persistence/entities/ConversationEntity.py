from typing import List

from mongoengine import Document, EmbeddedDocument, EmbeddedDocumentField, ListField, StringField, BooleanField


class User(EmbeddedDocument):
    user_id = StringField(required=True)


class Content(EmbeddedDocument):
    text = StringField(required=True)
    type = StringField(required=True)


class Message(EmbeddedDocument):
    user_id = StringField(required=True)
    content = ListField(EmbeddedDocumentField(Content), required=True)
    role = StringField(required=True)
    name = StringField(required=True)


class ConversationEntity(Document):
    """
    Represents a persistent conversation thread between users and agents over the Azure Bot Service.

    ### Purpose
    - Stores conversation history, including user messages and AI responses.
    - Tracks participants involved in a given conversation.
    - Enables retrieval of prior messages for contextual interactions.

    ### Usage
    This class enables AI agents to maintain contextual awareness across multiple exchanges,
    ensuring better response generation and user experience.
    """

    meta = {
        "collection": "conversations",
        "strict": True,
    }
    is_mentioned = BooleanField(default=False)
    conversation_id = StringField(required=True)
    messages = ListField(EmbeddedDocumentField(Message), required=False)

    @classmethod
    def create_conversation(
        cls,
        conversation_id: str,
        messages: List[Message],
    ) -> "ConversationEntity":
        conversation = cls(conversation_id=conversation_id, messages=messages)
        return conversation.save()

    @classmethod
    def add_messages_to_conversation(
        cls,
        conversation_id: str,
        messages: List[Message],
    ) -> "ConversationEntity":
        conversation = cls.get_conversation_by_conversation_id(conversation_id)
        if conversation is None:
            conversation = cls.create_conversation(conversation_id, [])
        conversation.messages.extend(messages)
        return conversation.save()

    @classmethod
    def get_conversation_by_conversation_id(cls, conversation_id: str) -> "ConversationEntity":
        return cls.objects().filter(conversation_id=conversation_id).first()

    @classmethod
    def get_messages_by_conversation_id(cls, conversation_id: str) -> ListField:
        conversation = cls.get_conversation_by_conversation_id(conversation_id)
        return conversation.messages

    @classmethod
    def get_conversation_is_mentioned(cls, conversation_id: str) -> bool:
        conversation = cls.get_conversation_by_conversation_id(conversation_id)
        return conversation.is_mentioned

    @classmethod
    def set_conversation_is_mentioned(cls, conversation_id: str, is_mentioned: bool) -> "ConversationEntity":
        conversation = cls.get_conversation_by_conversation_id(conversation_id)
        conversation.is_mentioned = is_mentioned
        return conversation.save()
