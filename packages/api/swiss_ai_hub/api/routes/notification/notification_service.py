import math

from bson import ObjectId
from fastapi import HTTPException
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.infrastructure import trace_fn
from swiss_ai_hub.core.persistence.notification.notification_entity import NotificationEntity

from swiss_ai_hub.api.routes.notification.dto.notification_dto import (
    NotificationDTO,
)
from swiss_ai_hub.api.routes.notification.dto.paginated_notifications_response import PaginatedNotificationsResponse
from swiss_ai_hub.api.routes.notification.dto.update_notification_request import (
    BulkUpdateNotificationRequest,
    UpdateNotificationRequest,
)


class NotificationService:
    """Service layer for handling notification-related business logic."""

    @staticmethod
    @trace_fn
    async def get_notifications_for_user(
        user_id: str, page: int, page_size: int, t: LocaleHandler, **filters
    ) -> PaginatedNotificationsResponse:
        """Retrieves a paginated list of notifications with optional filters."""
        entities, total = await NotificationEntity.get_for_user(
            user_id=user_id, page=page, page_size=page_size, **filters
        )
        dtos = [NotificationDTO.from_entity(entity=entity, t=t) for entity in entities]
        return PaginatedNotificationsResponse(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if page_size > 0 else 0,
            notifications=dtos,
        )

    @staticmethod
    @trace_fn
    async def update_one(
        notification_id: str, user_id: str, updates: UpdateNotificationRequest, t: LocaleHandler
    ) -> NotificationDTO:
        """Updates a single notification for a user."""
        notifications = (
            await NotificationEntity.find_for_user(user_id, [ObjectId(notification_id)])
            if ObjectId.is_valid(notification_id)
            else []
        )
        if not notifications:
            raise HTTPException(status_code=404, detail="Notification not found.")
        notification = notifications[0]

        if updates.read:
            await notification.mark_as_read()
        if updates.done:
            await notification.mark_as_done()

        return NotificationDTO.from_entity(entity=notification, t=t)

    @staticmethod
    @trace_fn
    async def update_many(
        user_id: str, bulk_updates: BulkUpdateNotificationRequest, t: LocaleHandler
    ) -> list[NotificationDTO]:
        """Updates multiple notifications and returns the updated objects."""
        update_data = bulk_updates.updates
        notification_ids = bulk_updates.notification_ids

        notifications_to_update = await NotificationEntity.find_for_user(
            user_id,
            [ObjectId(notification_id) for notification_id in notification_ids if ObjectId.is_valid(notification_id)],
        )

        if not notifications_to_update:
            return []

        ids_to_update = [n.id for n in notifications_to_update]

        if update_data.read:
            await NotificationEntity.mark_multiple_as_read(user_id, ids_to_update)
        if update_data.done:
            await NotificationEntity.mark_multiple_as_done(user_id, ids_to_update)

        updated_notifications = await NotificationEntity.find_for_user(user_id, ids_to_update)
        return [NotificationDTO.from_entity(entity=n, t=t) for n in updated_notifications]
