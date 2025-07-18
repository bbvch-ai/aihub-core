from datetime import UTC, datetime

from mongoengine import (
    BooleanField,
    DateTimeField,
    Document,
    EmbeddedDocument,
    EmbeddedDocumentField,
    ListField,
    StringField,
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
    Tracks conversation IDs to distinguish between expired and explicitly deleted conversations.

    This class solves the problem of determining whether a missing conversation was:
    1. Automatically expired by the TTL mechanism (after 1 month of inactivity), or
    2. Explicitly deleted by a user in Microsoft Teams

    The explicitly_deleted flag exists specifically to handle Microsoft Teams' behavior:
    In Teams, when a user deletes a conversation, they are starting fresh with the same
    conversation ID. Without tracking this flag, the system would incorrectly show an
    "expired conversation" message when a Teams user deliberately deleted their chat history.

    Usage:
    - Call track_conversation() whenever processing a message in an active conversation
    - Call mark_explicitly_deleted() when detecting a Teams conversation was deliberately deleted
      (typically in the on_conversation_update_activity handler for Teams)
    - Use should_show_expiration_message() to determine if the "conversation expired"
      notification should be shown to the user

    This enables providing appropriate user feedback only when conversations truly
    expired due to inactivity, not when they were deliberately reset in Teams.
    """

    meta = {"collection": "conversation_trackers", "strict": True}
    conversation_id = StringField(required=True, unique=True)
    created_at = DateTimeField(default=lambda: datetime.now(UTC))
    explicitly_deleted = BooleanField(default=False)

    @classmethod
    def track_conversation(cls, conversation_id: str):
        cls.objects(conversation_id=conversation_id).update_one(
            upsert=True,
            set__conversation_id=conversation_id,
            set__explicitly_deleted=False,
            set_on_insert__created_at=datetime.now(UTC),
        )

    @classmethod
    def mark_explicitly_deleted(cls, conversation_id: str):
        cls.objects(conversation_id=conversation_id).update_one(
            upsert=True, set__conversation_id=conversation_id, set__explicitly_deleted=True
        )

    @classmethod
    def should_show_expiration_message(cls, conversation_id: str) -> bool:
        tracker = cls.objects(conversation_id=conversation_id).first()
        exists_now = ConversationEntity.get_conversation_by_conversation_id(conversation_id) is not None

        return tracker is not None and not tracker.explicitly_deleted and not exists_now


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
        "indexes": [
            {"fields": ["conversation_id"], "unique": True},
        ],
    }
    is_mentioned = BooleanField(default=False)
    conversation_id = StringField(required=True)
    messages = ListField(EmbeddedDocumentField(Message), required=False)
    last_activity = DateTimeField(default=datetime.utcnow)

    @classmethod
    def update_ttl_index(cls, conversation_ttl_days: float):
        collection = cls._get_collection()

        # Convert days to seconds
        ttl_seconds = int(conversation_ttl_days * 24 * 60 * 60)

        # Drop existing TTL index if it exists
        try:
            collection.drop_index("last_activity_1")
        except Exception:
            # Index might not exist, that's ok
            pass

        # Create new TTL index
        collection.create_index([("last_activity", 1)], expireAfterSeconds=ttl_seconds)

    @classmethod
    def create_conversation(
        cls,
        conversation_id: str,
        messages: list[Message],
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
        messages: list[Message],
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
