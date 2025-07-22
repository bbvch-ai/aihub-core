from typing import Annotated

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.routes.Controller import Controller
from fastapi import HTTPException, Path, Query, Security
from mongoengine import DoesNotExist

from aihub_api.routes.notification.dto.NotificationDTO import (
    NotificationDTO,
)
from aihub_api.routes.notification.dto.PaginatedNotificationsResponse import PaginatedNotificationsResponse
from aihub_api.routes.notification.dto.UpdateNotificationRequest import (
    BulkUpdateNotificationRequest,
    UpdateNotificationRequest,
)
from aihub_api.routes.notification.NotificationService import NotificationService


class NotificationController(Controller):
    """Controller for managing user notifications."""

    name = LocaleString(en="Notifications")
    description = LocaleString(en="View and manage notifications")
    icon = "mdi:bell-outline"

    def __init__(self, *, auth: AuthHandler, route: str = "/notifications", **kwargs):
        super().__init__(auth=auth, route=route, **kwargs)

    def get_notifications(self, route: str = "/") -> "NotificationController":
        @self.router.get(route, tags=self.tags, response_model=PaginatedNotificationsResponse)
        async def get_notifications(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            page: int = Query(1, ge=1),
            page_size: int = Query(20, ge=1, le=100),
            types: list[str] | None = Query(None),
            severities: list[str] | None = Query(None),
            read: bool | None = Query(None),
            done: bool | None = Query(None),
        ):
            """Retrieves a paginated list of notifications with optional filters."""
            filters = {"types": types, "severities": severities, "read": read, "done": done}
            return NotificationService.get_notifications_for_user(user.id, page, page_size, **filters)

        return self

    def update_notification(self, route: str = "/{notification_id}") -> "NotificationController":
        @self.router.patch(route, tags=self.tags, response_model=NotificationDTO)
        async def update_notification(
            notification_id: str = Path(..., description="The ID of the notification to update."),
            updates: UpdateNotificationRequest = ...,
            user: UserIdentity = Security(self.user_with_permission("aihub.user.?>")),
        ) -> NotificationDTO:
            """Partially updates a notification (e.g., marks it as read or done)."""
            try:
                return NotificationService.update_one(notification_id, user.id, updates)
            except DoesNotExist:
                raise HTTPException(status_code=404, detail="Notification not found.")

        return self

    def update_notifications(self, route: str = "/") -> "NotificationController":
        @self.router.patch(route, tags=self.tags, response_model=list[NotificationDTO])
        async def update_notifications_bulk(
            bulk_updates: BulkUpdateNotificationRequest,
            user: UserIdentity = Security(self.user_with_permission("aihub.user.?>")),
        ) -> list[NotificationDTO]:
            """Partially updates a list of notifications (e.g., marks them as read or done)."""
            return NotificationService.update_many(user.id, bulk_updates)

        return self
