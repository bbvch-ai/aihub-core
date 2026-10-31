from typing import Self

from beanie import Document
from pymongo import ASCENDING, IndexModel

from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn


class OpenWebuiAccountEntity(Document):
    """Which OpenWebUI account belongs to which of our users.

    OpenWebUI's code sandbox keys each user's home by the OpenWebUI user id, so an agent running code for a user
    needs that id to work in the same home the user's chats and Files panel see. The group sync matches the accounts
    anyway and records the result here.
    """

    user_id: str
    openwebui_id: str

    class Settings:
        name = "openwebui_accounts"
        keep_nulls = False
        indexes = [IndexModel([("user_id", ASCENDING)], unique=True)]

    @classmethod
    @trace_fn
    async def record_all(cls, openwebui_ids_by_user: dict[str, str]) -> None:
        """Replace the recorded accounts with this sync's matches; a user no longer matched loses their entry."""
        await cls.find({"user_id": {"$nin": list(openwebui_ids_by_user)}}).delete()
        collection = cls.get_pymongo_collection()
        for user_id, openwebui_id in openwebui_ids_by_user.items():
            await collection.update_one({"user_id": user_id}, {"$set": {"openwebui_id": openwebui_id}}, upsert=True)

    @classmethod
    @trace_fn
    async def openwebui_id_of(cls, user_id: str) -> str | None:
        account: Self | None = await cls.find_one({"user_id": user_id})
        return account.openwebui_id if account else None
