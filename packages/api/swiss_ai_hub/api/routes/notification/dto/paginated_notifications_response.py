from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.api.routes.notification.dto.notification_dto import NotificationDTO


class PaginatedNotificationsResponse(BaseModel):
    """A paginated response container for notifications."""

    total: Annotated[int, Field(description="The total number of notifications matching the filter criteria.")]
    page: Annotated[int, Field(description="The current page number (1-indexed).")]
    page_size: Annotated[int, Field(description="The number of notifications requested per page.")]
    total_pages: Annotated[int, Field(description="The total number of pages available based on the page size.")]
    notifications: Annotated[
        list[NotificationDTO], Field(description="The list of notifications for the current page.")
    ]
