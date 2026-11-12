import logging
import re
from datetime import UTC, datetime
from typing import Self

from beanie import Document
from pydantic import BaseModel, Field
from pymongo import ASCENDING, IndexModel

logger = logging.getLogger(__name__)

TTL_INDEX_NAME = "last_activity_1"


class Content(BaseModel):
    text: str
    type: str


class Message(BaseModel):
    user_id: str
    content: list[Content]
    role: str
    name: str


def _clean_conversation_id(conversation_id: str, bot_id: str) -> str:
    """
    Clean the conversation ID by removing the bot and team ID prefix from Slack conversation IDs.

    Slack conversation IDs have the format: B[bot_id]:T[team_id]:C[channel_id] or
    B[bot_id]:T[team_id]:C[channel_id]:timestamp for threaded messages.

    The bot_id from turn_context.activity.recipient.id has the format: B[bot_id]:T[team_id]
    """
    slack_thread_re = re.compile(r"^(B[0-9A-Z]+:T[0-9A-Z]+):(C[0-9A-Z]+(?::\d+[.]\d+)?)$")
    match = slack_thread_re.match(conversation_id)
    if match:
        extracted_bot_team_id = match.group(1)
        if extracted_bot_team_id != bot_id:
            logger.warning(f"Bot:Team ID mismatch: extracted '{extracted_bot_team_id}' != expected '{bot_id}'")
            raise ValueError(
                f"Bot:Team ID mismatch: extracted '{extracted_bot_team_id}' does not match expected '{bot_id}'"
            )
        return match.group(2)
    return conversation_id


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

    conversation_id: str
    bot_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    explicitly_deleted: bool = False

    class Settings:
        name = "bot_conversation_trackers"
        keep_nulls = False
        indexes = [IndexModel([("conversation_id", ASCENDING), ("bot_id", ASCENDING)], unique=True)]

    @classmethod
    async def track_conversation(cls, conversation_id: str, bot_id: str) -> None:
        conversation_id = _clean_conversation_id(conversation_id, bot_id)
        await cls.get_pymongo_collection().update_one(
            {"conversation_id": conversation_id, "bot_id": bot_id},
            {
                "$set": {"conversation_id": conversation_id, "bot_id": bot_id, "explicitly_deleted": False},
                "$setOnInsert": {"created_at": datetime.now(UTC)},
            },
            upsert=True,
        )

    @classmethod
    async def mark_explicitly_deleted(cls, conversation_id: str, bot_id: str) -> None:
        conversation_id = _clean_conversation_id(conversation_id, bot_id)
        await cls.get_pymongo_collection().update_one(
            {"conversation_id": conversation_id, "bot_id": bot_id},
            {"$set": {"conversation_id": conversation_id, "bot_id": bot_id, "explicitly_deleted": True}},
            upsert=True,
        )

    @classmethod
    async def get_tracker(cls, conversation_id: str, bot_id: str) -> Self | None:
        conversation_id = _clean_conversation_id(conversation_id, bot_id)
        return await cls.find_one({"conversation_id": conversation_id, "bot_id": bot_id})

    @classmethod
    async def delete_tracker(cls, conversation_id: str, bot_id: str) -> None:
        conversation_id = _clean_conversation_id(conversation_id, bot_id)
        await cls.find({"conversation_id": conversation_id, "bot_id": bot_id}).delete()

    @classmethod
    async def should_show_expiration_message(cls, conversation_id: str, bot_id: str) -> bool:
        tracker = await cls.get_tracker(conversation_id, bot_id)
        exists_now = await ConversationEntity.get_conversation_by_conversation_id(conversation_id, bot_id) is not None

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

    is_mentioned: bool = False
    conversation_id: str
    bot_id: str
    messages: list[Message] = Field(default_factory=list)
    last_activity: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "bot_conversations"
        keep_nulls = False
        use_state_management = True
        state_management_replace_objects = True
        indexes = [IndexModel([("conversation_id", ASCENDING), ("bot_id", ASCENDING)], unique=True)]

    @classmethod
    async def update_ttl_index(cls, conversation_ttl_days: float) -> None:
        """Recreates the TTL index, since MongoDB cannot change the expiry of an existing one in place."""
        collection = cls.get_pymongo_collection()
        if TTL_INDEX_NAME in await collection.index_information():
            await collection.drop_index(TTL_INDEX_NAME)

        ttl_seconds = int(conversation_ttl_days * 24 * 60 * 60)
        await collection.create_index([("last_activity", ASCENDING)], expireAfterSeconds=ttl_seconds)

    @classmethod
    async def create_conversation(cls, conversation_id: str, bot_id: str, messages: list[Message]) -> Self:
        conversation_id = _clean_conversation_id(conversation_id, bot_id)
        conversation = cls(
            conversation_id=conversation_id, bot_id=bot_id, messages=messages, last_activity=datetime.now(UTC)
        )
        return await conversation.insert()

    @classmethod
    async def delete_conversation_if_exists(cls, conversation_id: str, bot_id: str) -> None:
        conversation = await cls.get_conversation_by_conversation_id(conversation_id, bot_id)
        if conversation is None:
            logger.debug(f"Conversation {conversation_id} for bot {bot_id} does not exist.")
            return
        await conversation.delete()

    @classmethod
    async def add_messages_to_conversation(cls, conversation_id: str, bot_id: str, messages: list[Message]) -> Self:
        conversation = await cls.get_conversation_by_conversation_id(conversation_id, bot_id)
        if conversation is None:
            conversation = await cls.create_conversation(conversation_id, bot_id, [])
        conversation.messages = [*conversation.messages, *messages]
        conversation.last_activity = datetime.now(UTC)
        await conversation.save_changes()
        return conversation

    @classmethod
    async def get_conversation_by_conversation_id(cls, conversation_id: str, bot_id: str) -> Self | None:
        conversation_id = _clean_conversation_id(conversation_id, bot_id)
        return await cls.find_one({"conversation_id": conversation_id, "bot_id": bot_id})

    @classmethod
    async def get_messages_by_conversation_id(cls, conversation_id: str, bot_id: str) -> list[Message]:
        conversation = await cls.get_conversation_by_conversation_id(conversation_id, bot_id)
        return conversation.messages

    @classmethod
    async def get_conversation_is_mentioned(cls, conversation_id: str, bot_id: str) -> bool:
        conversation = await cls.get_conversation_by_conversation_id(conversation_id, bot_id)
        return conversation.is_mentioned

    @classmethod
    async def set_conversation_is_mentioned(cls, conversation_id: str, bot_id: str, is_mentioned: bool) -> Self:
        conversation = await cls.get_conversation_by_conversation_id(conversation_id, bot_id)
        conversation.is_mentioned = is_mentioned
        await conversation.save_changes()
        return conversation
