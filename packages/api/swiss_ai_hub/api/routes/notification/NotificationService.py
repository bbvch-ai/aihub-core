import math

from mongoengine import DoesNotExist
from swiss_ai_hub.core.i18n.LocaleHandler import LocaleHandler
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.persistence.notification.NotificationEntity import NotificationEntity

from swiss_ai_hub.api.routes.notification.dto.NotificationDTO import (
    NotificationDTO,
)
from swiss_ai_hub.api.routes.notification.dto.PaginatedNotificationsResponse import PaginatedNotificationsResponse
from swiss_ai_hub.api.routes.notification.dto.UpdateNotificationRequest import (
    BulkUpdateNotificationRequest,
    UpdateNotificationRequest,
)


class NotificationService:
    """Service layer for handling notification-related business logic."""

    @staticmethod
    @trace_fn
    def get_notifications_for_user(
        user_id: str, page: int, page_size: int, t: LocaleHandler, **filters
    ) -> PaginatedNotificationsResponse:
        """Retrieves a paginated list of notifications with optional filters."""
        entities, total = NotificationEntity.get_for_user(user_id=user_id, page=page, page_size=page_size, **filters)
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
    def update_one(
        notification_id: str, user_id: str, updates: UpdateNotificationRequest, t: LocaleHandler
    ) -> NotificationDTO:
        """Updates a single notification for a user."""
        notification = NotificationEntity.objects(id=notification_id, user_id=user_id).first()
        if not notification:
            raise DoesNotExist("Notification not found.")

        if updates.read:
            notification.mark_as_read()
        if updates.done:
            notification.mark_as_done()

        return NotificationDTO.from_entity(entity=notification, t=t)

    @staticmethod
    @trace_fn
    def update_many(
        user_id: str, bulk_updates: BulkUpdateNotificationRequest, t: LocaleHandler
    ) -> list[NotificationDTO]:
        """Updates multiple notifications and returns the updated objects."""
        update_data = bulk_updates.updates
        notification_ids = bulk_updates.notification_ids

        notifications_to_update = NotificationEntity.objects(id__in=notification_ids, user_id=user_id).all()

        if not notifications_to_update:
            return []

        ids_to_update = [n.id for n in notifications_to_update]

        if update_data.read:
            NotificationEntity.mark_multiple_as_read(user_id, ids_to_update)
        if update_data.done:
            NotificationEntity.mark_multiple_as_done(user_id, ids_to_update)

        updated_notifications = NotificationEntity.objects(id__in=ids_to_update).all()
        return [NotificationDTO.from_entity(entity=n, t=t) for n in updated_notifications]
