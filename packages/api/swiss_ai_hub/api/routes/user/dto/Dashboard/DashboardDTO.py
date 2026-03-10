from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.api.routes.user.dto.Dashboard.DashboardItemDTO import DashboardItemDTO


class DashboardDTO(BaseModel):
    minRow: Annotated[
        int | None,
        Field(description="Minimum number of rows in the grid."),
    ] = None
    margin: Annotated[int | None, Field(description="Gap between grid items in pixels.")] = None
    column: Annotated[int | None, Field(description="Number of columns in the grid.")] = None
    cellHeight: Annotated[int | None, Field(description="Height of one cell in pixels.")] = None
    children: Annotated[
        list[DashboardItemDTO],
        Field(
            description="List of widgets (dashboard items) within the grid.",
        ),
    ] = []
