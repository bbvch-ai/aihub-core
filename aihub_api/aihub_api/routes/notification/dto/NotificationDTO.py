from datetime import datetime
from pydantic import BaseModel, Field, StringConstraints
from typing import Annotated, Literal

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.persistence.notification.NotificationEntity import NotificationEntity

NotificationTypeAPI = Literal["success", "info", "warning", "danger"]

NotificationSeverityAPI = Literal["low", "medium", "high"]

NotificationLink = Annotated[str, StringConstraints(pattern=r"^/.*$")]


class UpdateNotificationRequest(BaseModel):
    """Request model for partially updating a notification."""
    read: Annotated[bool | None, Field(description="The new 'read' status of the notification.")] = None
    done: Annotated[bool | None, Field(description="The new 'done' status for the notification's task.")] = None


class NotificationDTO(BaseModel):
    """Data Transfer Object for a notification."""

    id: Annotated[str, Field(description="The unique identifier of the notification.")]
    title: Annotated[LocaleString, Field(description="The internationalized title of the notification.")]
    message: Annotated[LocaleString, Field(description="The internationalized content of the notification.")]
    read: Annotated[bool, Field(description="Indicates if the notification has been read by the user.")]
    done: Annotated[bool, Field(description="Indicates if the task associated with the notification has been completed.")]
    type: Annotated[NotificationTypeAPI, Field(description="Categorizes the notification for visual representation (e.g., icon and color).")]
    severity: Annotated[NotificationSeverityAPI, Field(description="The priority level of the notification.")]
    link: Annotated[NotificationLink | None, Field(description="An optional internal link to navigate to the relevant resource.")] = None
    created_at: Annotated[datetime, Field(description="The timestamp when the notification was created.")]

    @classmethod
    def from_entity(cls, entity: NotificationEntity) -> "NotificationDTO":
        """Creates a NotificationDTO from a NotificationEntity."""
        return cls(
            id=str(entity.id),
            title=entity.title,
            message=entity.message,
            read=entity.read,
            done=entity.done,
            type=entity.type,
            severity=entity.severity,
            link=entity.link,
            created_at=entity.created_at,
        )


class PaginatedNotificationsResponse(BaseModel):
    """A paginated response container for notifications."""
    total: Annotated[int, Field(description="The total number of notifications matching the filter criteria.")]
    page: Annotated[int, Field(description="The current page number (1-indexed).")]
    page_size: Annotated[int, Field(description="The number of notifications requested per page.")]
    total_pages: Annotated[int, Field(description="The total number of pages available based on the page size.")]
    notifications: Annotated[list[NotificationDTO], Field(description="The list of notifications for the current page.")]