import math
from mongoengine import DoesNotExist

from aihub_api.routes.notification.dto.NotificationDTO import (
    NotificationDTO,
    PaginatedNotificationsResponse,
    UpdateNotificationRequest
)
from aihub_lib.persistence.notification.NotificationEntity import NotificationEntity


class NotificationService:
    """Service layer for handling notification-related business logic."""

    @staticmethod
    def get_notifications_for_user(user_id: str, page: int, page_size: int, **filters) -> PaginatedNotificationsResponse:
        """Retrieves a paginated list of notifications with optional filters."""
        entities, total = NotificationEntity.get_for_user(user_id=user_id, page=page, page_size=page_size, **filters)
        dtos = [NotificationDTO.from_entity(entity) for entity in entities]
        return PaginatedNotificationsResponse(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if page_size > 0 else 0,
            notifications=dtos,
        )

    @staticmethod
    def update_notification(notification_id: str, user_id: str, updates: UpdateNotificationRequest) -> NotificationDTO:
        """Updates a single notification's read or done status."""
        notification = NotificationEntity.objects(id=notification_id, user_id=user_id).first()
        if not notification:
            raise DoesNotExist("Notification not found.")

        update_data = updates.model_dump(exclude_unset=True)
        if not update_data:
            return NotificationDTO.from_entity(notification)

        notification.modify(**update_data)
        return NotificationDTO.from_entity(notification)

    @staticmethod
    def mark_all_as_read(user_id: str) -> int:
        """Marks all of a user's notifications as read."""
        return NotificationEntity.mark_all_as_read(user_id=user_id)

    @staticmethod
    def mark_all_as_done(user_id: str) -> int:
        """Marks all of a user's notifications as done."""
        return NotificationEntity.mark_all_as_done(user_id=user_id)