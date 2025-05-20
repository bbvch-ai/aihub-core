from typing import List, Optional

from pydantic import BaseModel, Field
from typing_extensions import Annotated

from aihub_api.routes.user.dto.Dashboard.DashboardItemDTO import DashboardItemDTO


class DashboardDTO(BaseModel):
    minRow: Annotated[
        Optional[int],
        Field(description="Minimum number of rows in the grid."),
    ] = None
    margin: Annotated[Optional[int], Field(description="Gap between grid items in pixels.")] = None
    column: Annotated[Optional[int], Field(description="Number of columns in the grid.")] = None
    cellHeight: Annotated[Optional[int], Field(description="Height of one cell in pixels.")] = None
    children: Annotated[
        List[DashboardItemDTO],
        Field(
            default_factory=list,
            description="List of widgets (dashboard items) within the grid.",
        ),
    ]
