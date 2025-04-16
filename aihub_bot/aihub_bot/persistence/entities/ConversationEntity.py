from datetime import datetime, timezone
from typing import List

from mongoengine import (
    BooleanField,
    Document,
    EmbeddedDocument,
    EmbeddedDocumentField,
    ListField,
    StringField,
    DateTimeField,
)


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


class ConversationTracker(Document):
    """
    Lightweight document to track all conversation IDs that have ever existed.
    This allows us to detect when a user tries to resume an expired conversation.
    """

    meta = {"collection": "conversation_trackers", "strict": True}
    conversation_id = StringField(required=True, unique=True)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    @classmethod
    def track_conversation(cls, conversation_id: str):
        """Create a tracker for this conversation if it doesn't exist"""
        cls.objects(conversation_id=conversation_id).update_one(
            upsert=True,  # Create if doesn't exist
            set__conversation_id=conversation_id,
            set_on_insert__created_at=datetime.now(timezone.utc),
        )

    @classmethod
    def has_existed_before(cls, conversation_id: str) -> bool:
        """Check if this conversation ID has ever existed"""
        return cls.objects(conversation_id=conversation_id).count() > 0


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
        "collection": "bot_conversations",
        "strict": True,
        "indexes": [{"fields": ["last_activity"], "expireAfterSeconds": 2592000}],  # 30 days (1 month)
    }
    is_mentioned = BooleanField(default=False)
    conversation_id = StringField(required=True)
    messages = ListField(EmbeddedDocumentField(Message), required=False)
    last_activity = DateTimeField(default=datetime.utcnow)

    @classmethod
    def create_conversation(
        cls,
        conversation_id: str,
        messages: List[Message],
    ) -> "ConversationEntity":
        conversation = cls(conversation_id=conversation_id, messages=messages, last_activity=datetime.utcnow())
        return conversation.save()

    @classmethod
    def delete_conversation(cls, conversation_id: str) -> None:
        conversation = cls.get_conversation_by_conversation_id(conversation_id)
        conversation.delete()

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
        conversation.last_activity = datetime.utcnow()
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

    @classmethod
    def is_new_conversation(cls, conversation_id: str) -> bool:
        return cls.get_conversation_by_conversation_id(conversation_id) is None
