from datetime import datetime
from typing import Annotated, Literal, Self

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.persistence.notification.NotificationEntity import NotificationEntity
from pydantic import BaseModel, Field

NotificationTypeAPI = Literal["success", "info", "warn", "error"]

NotificationSeverityAPI = Literal["low", "medium", "high", "critical"]


class NotificationDTO(BaseModel):
    """Data Transfer Object for a notification."""

    id: Annotated[str, Field(description="The unique identifier of the notification.")]
    user_id: Annotated[str, Field(description="The unique identifier of the user associated with the notification.")]
    notification_group_id: Annotated[
        str | None, Field(description="The identifier of the notification group this notification belongs to.")
    ] = None
    title: Annotated[str, Field(description="The internationalized title of the notification.")]
    message: Annotated[str, Field(description="The internationalized content of the notification.")]
    read: Annotated[bool, Field(description="Indicates if the notification has been read by the user.")] = False
    done: Annotated[
        bool, Field(description="Indicates if the task associated with the notification has been completed.")
    ] = False
    type: Annotated[
        NotificationTypeAPI,
        Field(description="Categorizes the notification for visual representation (e.g., icon and color)."),
    ] = "info"
    severity: Annotated[NotificationSeverityAPI, Field(description="The priority level of the notification.")]
    link: Annotated[str, Field(description="A relative internal link to navigate to the relevant resource.")]
    created_at: Annotated[datetime, Field(description="The timestamp when the notification was created.")]

    @classmethod
    def from_entity(cls, entity: NotificationEntity, t: LocaleHandler) -> Self:
        """Creates a NotificationDTO from a NotificationEntity."""
        return cls(
            id=str(entity.id),
            user_id=entity.user_id,
            notification_group_id=entity.notification_group_id,
            title=t.extract(entity.title.to_mongo().to_dict()),
            message=t.extract(entity.message.to_mongo().to_dict()),
            read=entity.read,
            done=entity.done,
            type=entity.type,
            severity=entity.severity,
            link=entity.link,
            created_at=entity.created_at,
        )
