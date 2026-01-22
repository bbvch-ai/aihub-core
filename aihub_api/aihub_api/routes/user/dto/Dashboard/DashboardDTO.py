from typing import Annotated

from pydantic import BaseModel, Field

from aihub_api.routes.user.dto.Dashboard.DashboardItemDTO import DashboardItemDTO


class DashboardDTO(BaseModel):
    minRow: Annotated[
        int | None,
        Field(description="Minimum number of rows in the grid.", ge=0, le=1000),
    ] = None
    margin: Annotated[int | None, Field(description="Gap between grid items in pixels.", ge=0, le=100)] = None
    column: Annotated[int | None, Field(description="Number of columns in the grid.", ge=1, le=24)] = None
    cellHeight: Annotated[int | None, Field(description="Height of one cell in pixels.", ge=1, le=1000)] = None
    children: Annotated[
        list[DashboardItemDTO],
        Field(
            description="List of widgets (dashboard items) within the grid.",
            max_length=100,
        ),
    ] = []
