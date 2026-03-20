from typing import Annotated

from pydantic import BaseModel, Field


class UpdateNotificationRequest(BaseModel):
    """Request model for partially updating a notification."""

    read: Annotated[bool | None, Field(description="The new 'read' status of the notification.")] = None
    done: Annotated[bool | None, Field(description="The new 'done' status for the notification's task.")] = None


class BulkUpdateNotificationRequest(BaseModel):
    """Request model for updating multiple notifications at once."""

    notification_ids: Annotated[
        list[str],
        Field(description="The IDs of the notifications to update."),
    ]
    updates: Annotated[UpdateNotificationRequest, Field(description="The updates to apply to each notification.")]
