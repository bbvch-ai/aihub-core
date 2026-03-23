from typing import Annotated, Self

from fastapi import Depends, HTTPException, Query, Security
from mongoengine import DoesNotExist
from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.routes import Controller

from swiss_ai_hub.api.i18n.api_locale_string import ApiLocaleString
from swiss_ai_hub.api.i18n.dependencies.use_locale import use_locale
from swiss_ai_hub.api.routes.notification.dto.notification_dto import (
    NotificationDTO,
)
from swiss_ai_hub.api.routes.notification.dto.paginated_notifications_response import PaginatedNotificationsResponse
from swiss_ai_hub.api.routes.notification.dto.update_notification_request import (
    BulkUpdateNotificationRequest,
    UpdateNotificationRequest,
)
from swiss_ai_hub.api.routes.notification.notification_service import NotificationService


class NotificationController(Controller):
    """Controller for managing user notifications."""

    name = ApiLocaleString.from_i18n_path("api.controllers.notification.name")
    description = ApiLocaleString.from_i18n_path("api.controllers.notification.description")
    icon = "mage:notification-bell"

    def __init__(self, *, auth: AuthHandler, route: str = "/notifications", **kwargs):
        super().__init__(auth=auth, route=route, **kwargs)

    def get_notifications(self, route: str = "") -> Self:
        @self.router.get(route, tags=self.tags, response_model=PaginatedNotificationsResponse)
        async def get_notifications(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
            page: int = Query(1, ge=1),
            page_size: int = Query(20, ge=1, le=100),
            types: list[str] | None = Query(None),
            severities: list[str] | None = Query(None),
            read: bool | None = Query(None),
            done: bool | None = Query(None),
        ):
            """Retrieves a paginated list of notifications with optional filters."""
            filters = {"types": types, "severities": severities, "read": read, "done": done}
            return NotificationService.get_notifications_for_user(user.id, page, page_size, t, **filters)

        return self

    def update_notification(self, route: str = "/{notification_id}") -> Self:
        @self.router.patch(route, tags=self.tags, response_model=NotificationDTO)
        async def update_notification(
            notification_id: str,
            updates: UpdateNotificationRequest,
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> NotificationDTO:
            """Partially updates a notification (e.g., marks it as read or done)."""
            try:
                return NotificationService.update_one(
                    notification_id=notification_id, user_id=user.id, updates=updates, t=t
                )
            except DoesNotExist:
                raise HTTPException(status_code=404, detail="Notification not found.")

        return self

    def update_notifications(self, route: str = "/") -> Self:
        @self.router.patch(route, tags=self.tags, response_model=list[NotificationDTO])
        async def update_notifications_bulk(
            bulk_updates: BulkUpdateNotificationRequest,
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> list[NotificationDTO]:
            """Partially updates a list of notifications (e.g., marks them as read or done)."""
            return NotificationService.update_many(user_id=user.id, bulk_updates=bulk_updates, t=t)

        return self
