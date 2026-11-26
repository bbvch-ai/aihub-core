from datetime import UTC, datetime
from typing import Literal, Self

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn


class NotificationEntity(Document):
    """
    Represents a notification for a user in the database.
    """

    user_id: str
    notification_group_id: str | None = None
    title: LocaleString | None = None
    message: LocaleString | None = None
    read: bool = False
    done: bool = False
    type: Literal["info", "warn", "success", "error"] = "info"
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    link: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "notifications"
        keep_nulls = False
        use_state_management = True
        state_management_replace_objects = True
        indexes = [
            IndexModel([("user_id", ASCENDING)]),
            IndexModel([("user_id", ASCENDING), ("created_at", DESCENDING)]),
        ]

    @classmethod
    @trace_fn
    async def get_for_user(
        cls,
        user_id: str,
        page: int,
        page_size: int,
        types: list[str] | None = None,
        severities: list[str] | None = None,
        read: bool | None = None,
        done: bool | None = None,
        order_by: str = "-created_at",
    ) -> tuple[list[Self], int]:
        """Retrieves a paginated list of notifications, with optional filters."""
        criteria: dict = {"user_id": user_id}
        if types:
            criteria["type"] = {"$in": types}
        if severities:
            criteria["severity"] = {"$in": severities}
        if read is not None:
            criteria["read"] = read
        if done is not None:
            criteria["done"] = done

        offset = (page - 1) * page_size
        notifications = await cls.find(criteria).sort(order_by).skip(offset).limit(page_size).to_list()
        total = await cls.find(criteria).count()
        return notifications, total

    @classmethod
    @trace_fn
    async def find_for_user(cls, user_id: str, notification_ids: list[PydanticObjectId]) -> list[Self]:
        return await cls.find({"_id": {"$in": notification_ids}, "user_id": user_id}).to_list()

    @trace_fn
    async def mark_as_read(self) -> Self:
        self.read = True
        await self.save_changes()
        return self

    @trace_fn
    async def mark_as_done(self) -> Self:
        self.done = True
        await self.save_changes()
        return self

    @classmethod
    @trace_fn
    async def mark_multiple_as_read(cls, user_id: str, notification_ids: list[PydanticObjectId]) -> int:
        query = cls.find({"_id": {"$in": notification_ids}, "user_id": user_id})
        return (await query.update({"$set": {"read": True}})).modified_count

    @classmethod
    @trace_fn
    async def mark_multiple_as_done(cls, user_id: str, notification_ids: list[PydanticObjectId]) -> int:
        query = cls.find({"_id": {"$in": notification_ids}, "user_id": user_id})
        return (await query.update({"$set": {"done": True}})).modified_count
